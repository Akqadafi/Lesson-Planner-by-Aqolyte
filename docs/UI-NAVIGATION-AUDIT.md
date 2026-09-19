# Homepage and navigation audit

Date: September 17, 2026

Baseline: tagged release `v0.2.1` at commit `4ddcd0a`. The release remains on `main` and in
the private GitHub release. Experiments live on `codex/ui-navigation-redesign` and do not
replace the released homepage.

## Assessment

The lesson studio is the strongest part of the interface: its cream, forest-green, and white
system feels calm and appropriate for a planning tool. The older homepage uses Bootstrap,
bright blue rules, a gold logo, a different type system, and a separate navigation model. Moving
from the homepage to the studio feels like entering a different product.

The information architecture also has too many shallow stops. Home, About, Products, Features,
Contact, a second landing page, and a lesson-versus-worksheet chooser surround two competing
creation flows. The primary homepage button opens the modern studio while the older product flow
leads to the legacy forms. Visitors cannot easily tell which path represents the product.

Observed interface issues:

- The homepage delays all content with a 1.5-second opacity animation, creating a briefly blank
  interface and ignoring reduced-motion preference.
- The header is unusually tall relative to the small logo and short navigation.
- The homepage has large unused areas but gives little help choosing a task.
- On a 390-pixel viewport, the navigation is absent and centered text overflows or clips.
- About, Products, Features, and Contact contain too little information to justify top-level
  navigation positions.
- The footer still says 2024.
- The modern studio links only to Lesson studio and Worksheets, while handouts appear later and
  the older marketing navigation disappears entirely.
- Bootstrap, jQuery, Popper, and Google Fonts are fetched from third parties for otherwise simple
  pages. This adds dependency and offline-rendering risk without providing a coherent design.

## Recommended structure

Use one product-wide header and four plain destinations:

1. **Plan a lesson** — the modular lesson studio.
2. **Student materials** — lesson-linked handouts and teacher keys. When no lesson exists, explain
   that the teacher should start with a lesson.
3. **Quick worksheet** — the standalone legacy worksheet workflow, clearly named as a focused
   shortcut.
4. **How it works** — a concise explanation of Context → Lesson → Materials → Review and export.

Consolidate the useful About, Features, and product-description copy into the homepage and a
single help/about destination. Remove the second landing page and choice screen only after the
selected replacement is tested and existing routes are redirected safely.

## Preview options

### Option 1 — Teacher workspace (recommended)

Lead with “What are you planning today?” and three task cards. Show whether a saved lesson is
available. This is the clearest balance of product explanation, task discovery, and support for
returning teachers.

### Option 2 — Guided journey

Lead with a four-stage workflow: Context, Lesson, Materials, Review. This teaches the product well
but adds one conceptual layer before the teacher starts working.

### Option 3 — Studio first

Use a compact left navigation and dashboard. This is efficient for repeat use, but it is less
welcoming and gives first-time visitors less explanation.

## Decision gate

Choose one preview after checking desktop and mobile. Then replace the current homepage and shared
navigation, redirect or retire the redundant public routes, update route-inventory tests, and run
the full offline suite. The preview routes make no AI calls and do not alter saved drafts.

## Corporate homepage direction

The company and product layers are now treated separately on the experiment branch. `/` is an
Aqolyte LLC corporate homepage for its web, educational, and applied AI work. Lesson Planner is
presented as the first product and links into the existing application. The recommended Teacher
Workspace preview remains the proposed application dashboard, rather than the corporate home.

The next company-site pages are About, Products, a dedicated Lesson Planner product page, and
Contact. These should reuse the corporate header and footer. After those are complete, the
Lesson Planner should receive its own app shell and dashboard without duplicating the company
marketing navigation.

## Corporate navigation research and decision

The company pages now use one shared header and footer with Home, About, Products, and Contact.
The homepage explains the company and introduces Lesson Planner, while Products contains the
single direct launch into the application. This removes repeated Lesson Planner links that made
the homepage appear to offer more choices than it actually did.

This decision follows three established findings:

- Nielsen Norman Group observed that repeated navigation links make people scan duplicate
  choices and increase the effort needed to decide where to go:
  https://www.nngroup.com/articles/navigation-cognitive-strain/
- W3C guidance recommends descriptive link names and consistent identification for controls
  with the same function:
  https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-link-only.html
- Homepage guidance recommends a clear primary navigation area, grouped destinations, and
  direct access only for carefully selected high-priority tasks:
  https://www.nngroup.com/articles/113-design-guidelines-homepage-usability/

The corporate pages also use unique page titles, visible active-page states, a skip link, and
responsive navigation. The application remains a separate product layer and will receive its
own task-oriented shell in the next interface milestone.
