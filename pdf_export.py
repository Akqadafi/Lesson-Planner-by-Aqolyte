"""Local DOCX-to-PDF conversion with bounded work and isolated temporary profiles."""
import os
import shutil
import signal
import subprocess
import tempfile
import threading
from io import BytesIO
from pathlib import Path

_slots=threading.BoundedSemaphore(2)
_word_slot=threading.BoundedSemaphore(1)

class PDFExportError(RuntimeError):
    pass


def find_converter():
    backend=os.getenv('PDF_BACKEND','auto')
    if backend=='word':
        if os.name!='nt':raise PDFExportError('Word PDF conversion requires Windows. Use LibreOffice on this server.')
        return 'word'
    if backend not in ('libreoffice','auto'):raise PDFExportError('Unsupported PDF_BACKEND. Choose auto, libreoffice or word.')
    configured=os.getenv('LIBREOFFICE_PATH')
    candidates=[configured] if configured else [shutil.which('soffice.com'),shutil.which('soffice'),shutil.which('libreoffice'),r'C:\Program Files\LibreOffice\program\soffice.com']
    for candidate in candidates:
        if candidate and Path(candidate).is_file():return str(Path(candidate).resolve())
    if backend=='auto' and not configured and os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r'Word.Application\CLSID'):
                return 'word'
        except OSError:pass
    raise PDFExportError('PDF conversion is not configured. Install LibreOffice on the app server or set LIBREOFFICE_PATH. Word downloads are still available.')


def convert_docx(stream):
    executable=find_converter()
    slot=_word_slot if executable=='word' else _slots
    if not slot.acquire(timeout=2):
        raise PDFExportError('PDF conversion is busy. Please retry shortly or download Word instead.')
    try:
        with tempfile.TemporaryDirectory(prefix='lesson-pdf-',ignore_cleanup_errors=True) as directory:
            root=Path(directory);source=root/'document.docx';source.write_bytes(stream.getvalue())
            command=[executable,'-env:UserInstallation='+(root/'profile').as_uri(),'--headless','--nologo','--nodefault','--norestore','--convert-to','pdf:writer_pdf_Export','--outdir',str(root),str(source)]
            if executable=='word':
                command=['powershell.exe','-NoProfile','-NonInteractive','-File',str(Path(__file__).with_name('word_pdf.ps1')),'-InputPath',str(source),'-OutputPath',str(root/'document.pdf'),'-PidPath',str(root/'word.pid')]
            options={'stdout':subprocess.PIPE,'stderr':subprocess.PIPE}
            if os.name=='nt':options['creationflags']=subprocess.CREATE_NO_WINDOW
            else:options['start_new_session']=True
            try:
                process=subprocess.Popen(command,**options)
                try:process.communicate(timeout=60)
                except subprocess.TimeoutExpired:
                    if os.name=='nt':
                        pid_file=root/'word.pid'
                        if executable=='word' and pid_file.is_file():
                            word_pid=pid_file.read_text().strip()
                            if word_pid.isdigit() and int(word_pid)>0:
                                subprocess.run(['taskkill','/PID',word_pid,'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=10)
                        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=10)
                    else:os.killpg(process.pid,signal.SIGKILL)
                    process.communicate(timeout=10)
                    raise PDFExportError('PDF conversion took too long. Retry or download Word; your draft is unchanged.') from None
                output=root/'document.pdf'
                if process.returncode or not output.is_file():
                    raise PDFExportError('PDF conversion failed. Retry or download Word; your draft is unchanged.')
                data=output.read_bytes()
                if not data.startswith(b'%PDF-'):
                    raise PDFExportError('The converter did not return a valid PDF. Word downloads are still available.')
                return BytesIO(data)
            except PDFExportError:raise
            except (OSError,subprocess.SubprocessError):
                raise PDFExportError('PDF conversion could not run. Word downloads are still available.') from None
    finally:slot.release()
