# AICON'26 context for VisionForge

This is the event packet the product has to satisfy. The product rules live in [SRS.md](SRS.md). The decision record lives in [PROJECT.md](PROJECT.md).

Sources checked on Saturday 10 October 2026: the allocation email below, [aicon26.pk](https://www.aicon26.pk/), [aicon26.pk/modules](https://www.aicon26.pk/modules), the FAQ, the schedule page, and the public PDFs linked from those pages.

## Allocation email

> Dear Candidate,
>
> We hope you’re getting ready for Build With AI at AICON’26! Your domain and presentation slot have now been finalized.
>
> Your Allocation
>
> Team Name: VisionForge
> Allocated Domain: Health Operations
> Presentation Date: 11th October 2026
> Time Slot: 12:02 PM – 12:07 PM
> Venue: SEECS Lecture Hall
>
> About Your Module: Health Operations
> AI for diagnostics support, patient triage, hospital resource management, medical record processing, and public health monitoring.
> (These are only examples from your module, but you are free to choose your own idea.)
>
> Your team’s goal is to pick a specific, real-world problem within this domain and build a working Minimum Viable Product (MVP) powered by AI. Keep the standard flow in mind: Problem → Data/Input → AI Component → Solution → Impact.
>
> Presentation Details
> Each team gets 5 minutes to present. Please make sure your working MVP demo is loaded and tested on your team’s laptop before your slot. Be at the venue and ready a little before your start time, since slots run back to back and we won’t be able to delay them.
> Lastly, no slot swapping is permitted between teams under any circumstances unless approved beforehand due to a genuine emergency. On presentations day, we will only wait 2 minutes for a team to step up; if you are not present, your slot will be moved to the very end, and if time runs out, your team forfeits the demo. Keep track of your assigned time, build fair, and make every minute count!
>
> Also submission link will be provided to you on Day 2 so it is mandatory for you to come tomorrow.....
>
> Please read the Participant Guide and Rulebook carefully before the event.
>
> We wish your team the best of luck!

## What that email requires

- Module: Build with AI. Domain already assigned: Health Operations. The examples are diagnostics support, patient triage, hospital resource management, medical record processing, and public health monitoring. The team may choose its own problem inside that domain.
- Required story: Problem → Data/Input → AI Component → Solution → Impact.
- Demo: 5 minutes, 12:02–12:07 on Sunday 11 October 2026, SEECS Lecture Hall. The working MVP is loaded and tested on the team laptop before the slot.
- Be at the hall early. Slots are back to back and will not be delayed.
- No slot swapping unless the organizers approved an emergency in advance.
- On presentation day they wait 2 minutes. After that the slot moves to the end. If time runs out, the demo is forfeited.
- A submission link is handed out on Day 2. The email says attendance for that handoff is mandatory.
- The email tells the team to read a Participant Guide and a Rulebook. Those documents were not on the public site. See below.

## Public site, Build with AI

From [aicon26.pk/modules](https://www.aicon26.pk/modules), the Build with AI card:

- Tagline: "Data in. AI in the loop. Impact out."
- Team size 2–5. Fee Rs. 2,500–Rs. 4,500.
- "30hr build + 5 min demo."
- Teams are assigned one domain.
- MVP shape: data → AI → impact metric.
- Domains: Health Operations, Financial Operations, Agricultural Operations, EdTech & Workforce.
- "All four domains align with the SDGs outlined in the event brief. Solutions must demonstrate AI meaningfully embedded in the pipeline — not only as a UI layer."

The homepage card for the same module says "2–3 hr build" and "Pick one domain." That disagrees with the modules page. Treat the modules page plus the allocation email as binding: assigned domain, working MVP, measurable impact, AI inside the pipeline, 5-minute demo.

## Weekend schedule on the public site

SEECS, NUST, 9–11 October 2026. Hosted with GDGoC, ACM, NEC, and NHC.

- Friday 9 October — Opening Day. Registrations 9:00–13:00. Opening ceremony 14:00–17:00, Jinnah Auditorium (CIPS).
- Saturday 10 October — Competition Day. Module competitions 9:00–14:00. Culture Fest 14:00–17:00. Submission deadline for all modules at 12:00 AM, no extensions. Read that midnight as the end of Saturday unless an organizer says otherwise.
- Sunday 11 October — Finals. Pitchfest in the Seminar Hall and Build with AI in the Lecture Hall, 9:00–14:00. Closing ceremony 14:00–17:00, NICE Seminar Hall.

VisionForge's presentation slot sits inside the Sunday Lecture Hall block.

## What was not found

Searched the public site and the web on 10 October 2026.

- No Build with AI rulebook. These URLs 404: `/assets/docs/aicon26-build-with-ai-rulebook.pdf`, `/assets/docs/aicon26-participant-guide.pdf`, `/assets/docs/aicon26-rulebook.pdf`.
- The participants event plan PDF is public (`/assets/docs/aicon26-event-plan.pdf`, 4 pages) but it has no text layer. It was not readable.
- Build with AI has no published score weights.
- The percentages on the modules page (problem and solution 20%, pitch clarity 10%, business model 25%, innovation and impact 25%, market research 20%) belong to Pitchfest only.

The Pitchfest rulebook is public and is a different contest: a random idea drawn from a bowl, slides built in a 2-hour window, no working product. Do not follow it.

If someone is handed a Participant Guide or a Build with AI rulebook on site, add it to `docs/` and treat it as binding where it conflicts with this file.

## How a judge is likely to score this module

Inferred from the modules page and the email, not from a published rubric:

- The problem is a real Health Operations problem, not a generic diagnosis demo.
- The demo runs, on the laptop, inside five minutes.
- AI does the extraction. A rules layer may score and prioritize. A dashboard that only displays a prompt is the failure mode the modules page calls out.
- Impact is a number the team can show, with the limit of that number stated out loud.
- A clinical claim that the system diagnoses, orders treatment, or mutes an alarm will be marked down.

## Logistics that affect the build

- Present from the team laptop. Hall Wi-Fi is not the plan. The accepted runtime is a phone hotspot plus a cloud API key. The key stays in `.env` and out of git.
- One speaker. Rehearse with a phone timer.
- Submission may close Saturday night. Be at SEECS for the link.
- Demo order is Fixture A. Fixture B is the answer to "does every patient become a resus?"
