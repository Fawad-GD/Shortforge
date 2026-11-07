# Shorts AI Studio

MASTER PROMPT — BUILD A PROFESSIONAL AI SHORTS AUTOMATION PLATFORM

You are a senior full-stack engineer, AI/ML engineer, video-processing engineer, UI/UX designer, DevOps engineer, and QA engineer.

Build a production-ready AI video-to-shorts automation platform that can take a long-form video or supported video URL and automatically discover, create, caption, reframe, preview, and export as many high-quality short-form videos as the source content reasonably supports.

The result must be a REAL, WORKING APPLICATION.

Do NOT create a static website, fake dashboard, prototype, mockup, placeholder application, or UI-only demo.

Every major button, workflow, progress indicator, upload system, processing pipeline, preview, download function, and error state must actually work.

1. PRODUCT CONCEPT

The application converts:

LONG VIDEO
↓
TRANSCRIPTION
↓
CONTENT UNDERSTANDING
↓
MOMENT DETECTION
↓
CLIP CANDIDATE GENERATION
↓
QUALITY SCORING
↓
DUPLICATE REMOVAL
↓
SMART CLIP BOUNDARIES
↓
9:16 REFRAMING
↓
FACE/SPEAKER TRACKING
↓
CAPTIONS
↓
HOOK/TITLE GENERATION
↓
VIDEO RENDERING
↓
SHORTS LIBRARY
↓
DOWNLOAD INDIVIDUAL CLIPS OR ZIP

The platform should optimize for:

Maximum useful Shorts

High clip quality

Minimal duplicate content

Fast processing

Low infrastructure/API cost

Professional visual quality

Reliable processing

Easy operation

Scalability

Graceful failure recovery

Do not artificially generate a fixed number of clips.

If a 20-minute video contains 8 genuinely strong moments, produce around 8.

If a 2-hour video contains 40+ strong moments, allow 40+.

The objective is:

"Find every genuinely useful short-form moment without creating repetitive or low-quality clips."

2. IMPORTANT LEGAL / CONTENT RULE

The application must process content that the user owns, has permission to use, or is otherwise legally authorized to process.

Do not design the application around bypassing DRM, paywalls, private videos, authentication, or access restrictions.

For URL ingestion, support publicly accessible URLs through appropriate legal/technical methods.

Show a simple notice near URL input:

"Only process content you own or have permission to use."

3. TECHNOLOGY REQUIREMENTS

Use a practical production architecture.

Recommended stack:

FRONTEND:

React

TypeScript

Vite

Tailwind CSS

Modern component architecture

BACKEND:

Python

FastAPI

VIDEO:

FFmpeg

TRANSCRIPTION:

faster-whisper

VIDEO ANALYSIS:

OpenCV

PySceneDetect where useful

MediaPipe or another reliable face/subject tracking solution

AI:

Abstract the AI provider behind a provider interface.

Support local AI where practical.

Support optional API-based models.

Never hard-code the application to one AI provider.

QUEUE:

Redis

Celery or an equivalent reliable background job system

DATABASE:

PostgreSQL

STORAGE:

Local filesystem for development

S3-compatible object storage for production

CONTAINERIZATION:

Docker

Docker Compose for local development

The architecture must allow individual components to be replaced later.

4. DO NOT MAKE THESE MISTAKES

Do NOT:

Put the entire application into one enormous frontend file.

Process long videos synchronously inside an HTTP request.

Load entire videos into browser memory.

Send complete videos unnecessarily to an AI API.

Re-render the same source segment repeatedly.

Create 100 meaningless clips just to claim a high number.

use fake AI scores.

use fake progress percentages.

use placeholder video thumbnails.

pretend rendering completed when it failed.

silently fail.

lose jobs when the browser refreshes.

expose API keys in frontend code.

trust arbitrary uploaded filenames.

allow path traversal.

assume every video has a face.

assume every video is horizontal.

assume every speaker stays in one location.

assume every URL is downloadable.

assume every video has clear speech.

assume English is the only language.

assume every clip should be exactly 30 seconds.

crop important visual content accidentally.

5. APPLICATION STRUCTURE

Create these major areas:

Dashboard

Create Shorts

Processing Queue

Results / Shorts Library

Video Project Details

Settings

System Status / Diagnostics

Help / Documentation

Navigation should be simple.

Suggested sidebar:

Dashboard
Create
Projects
Processing
Shorts
Settings

6. PROFESSIONAL DASHBOARD

Create a polished professional dashboard.

Display:

Total projects

Videos processed

Shorts generated

Processing jobs

Storage used

Recent projects

Recent Shorts

System status

Example:

AI SHORTS STUDIO

Projects 12
Videos Processed 38
Shorts Generated 426
Processing 2

RECENT PROJECTS

Podcast Episode 42
126 Shorts Candidates
32 Shorts Generated

Interview with CEO
94 Candidates
21 Shorts Generated

[ + Create New Project ]

The dashboard must contain REAL database information.

Do not hard-code statistics.

7. CREATE PROJECT PAGE

Create a professional upload/import interface.

Allow:

OPTION A — UPLOAD

Drag and drop:

MP4
MOV
WEBM
M4V
AVI where supported

Show:

file name

file size

upload progress

cancel

remove

OPTION B — VIDEO URL

Input:

"Paste a supported public video URL"

Validate the URL before processing.

Show:

URL validation

loading state

metadata if available

title

duration

thumbnail where legally/technically available

Do not start expensive processing before validation.

8. PROJECT SETTINGS

Before processing, allow:

CLIP COUNT

Options:

Automatic / Maximum Useful
10
20
30
50
100
Custom

"Maximum Useful" must NOT mean blindly creating the maximum number.

It means:

"Find as many distinct high-quality clips as the source reasonably supports."

9. CLIP LENGTH

Allow:

Auto
15–30 sec
30–45 sec
45–60 sec
Custom

Recommended default:

20–60 seconds.

The system should determine natural boundaries.

Never cut a sentence in half unless unavoidable.

10. CONTENT STYLE

Allow user to select:

Podcast

Interview

Educational

Business

Motivation

Storytelling

Commentary

Comedy

News-style commentary

Gaming

General

Also allow:

AUTO DETECT

The selected category should influence scoring—not force the AI to manufacture moments.

11. CLIP QUALITY MODES

Provide:

BALANCED

Good quality / reasonable number.

MAXIMUM

Find the largest number of distinct useful clips.

QUALITY

Generate fewer but stricter clips.

CUSTOM

Allow advanced thresholds.

12. CAPTION SETTINGS

Allow:

Captions ON/OFF

Styles:

Clean

Bold

Highlight

Minimal

Dynamic

Settings:

Font

Size

Position

Maximum words per line

Highlight current word

Background

Shadow

Outline

Animation intensity

Default should be professional and readable.

Captions must be generated from actual transcript timestamps.

Do NOT fake word timing.

13. VIDEO FORMAT

Primary:

9:16

Resolution:

1080 × 1920

Also optionally support:

720 × 1280

16:9
1:1

But 9:16 should be the main Shorts workflow.

14. SMART REFRAMING

This is critical.

Do not simply center-crop every video.

Analyze:

faces

speakers

important subjects

motion

scene composition

For a podcast with two speakers:

Track the active speaker.

For a single speaker:

Keep the face appropriately framed.

For screen recordings:

Prioritize important screen content.

For gaming:

Preserve the important gameplay area.

For videos without faces:

Use intelligent subject/saliency detection.

If tracking confidence becomes low:

Fall back to stable framing instead of creating jitter.

15. CAMERA MOVEMENT

Avoid aggressive camera movement.

The crop should:

follow subjects smoothly

interpolate movement

avoid sudden jumps

avoid excessive zooming

avoid cutting faces

avoid losing important objects

Use smoothing.

The output should look professionally edited.

16. TRANSCRIPTION ENGINE

Use faster-whisper or an equivalent local transcription engine.

Required:

timestamps

segments

word timestamps where available

language detection

confidence where available

Store the transcript in the database.

Do not transcribe the same source video again unless necessary.

Cache transcription results.

17. TRANSCRIPT STRUCTURE

Convert transcript into structured data:

WORD

text

start

end

confidence

SENTENCE

text

start

end

PARAGRAPH / IDEA

text

start

end

topic

This structure will power clip discovery.

18. AI CLIP DISCOVERY

Do NOT simply ask an LLM:

"Give me 10 clips."

Instead:

Segment transcript into meaningful ideas.

Generate candidate windows.

Score candidate windows.

Expand candidates to natural sentence boundaries.

Compare candidates.

Remove duplicates.

Re-score final candidates.

The system should search the entire video.

19. WHAT MAKES A GOOD SHORT?

Create a scoring system using multiple factors.

Possible factors:

HOOK
VALUE
CURIOSITY
EMOTIONAL IMPACT
STANDALONE CONTEXT
COMPLETENESS
ENTERTAINMENT
SURPRISE
STORY ARC
ACTIONABLE INFORMATION
ENDING STRENGTH
VISUAL QUALITY
AUDIO QUALITY
DUPLICATION PENALTY

Example conceptual score:

FinalScore =
HookScore

ValueScore

CuriosityScore

CompletenessScore

EntertainmentScore

VisualScore

EndingScore

DuplicatePenalty

ContextDependencyPenalty

Do NOT blindly use this exact formula if testing demonstrates a better approach.

Make the scoring system configurable.

20. CLIP MUST WORK WITHOUT THE ORIGINAL VIDEO CONTEXT

A major requirement:

A clip should make sense when watched independently.

Penalize clips that start with:

"and then..."
"as I said..."
"he..."
"she..."
"this..."
"that..."

unless the missing context is not actually necessary.

If necessary, expand the beginning of the clip to include the required context.

21. STRONG HOOK DETECTION

Look for:

surprising statements

questions

strong claims

unexpected facts

mistakes

lessons

controversial-but-permitted discussion

emotional moments

stories

punchlines

useful advice

curiosity gaps

strong conclusions

Do not manufacture controversial statements.

22. NATURAL CLIP BOUNDARIES

The system should intelligently determine:

START

before the hook if context is required

END

after the conclusion/punchline

Avoid:

cutting mid-word

cutting mid-sentence

cutting immediately after the hook

ending before the useful information

unnecessary dead air

Trim silence where appropriate.

23. SILENCE DETECTION

Detect excessive silence.

Remove only unnecessary silence.

Do not destroy natural pauses.

Allow configurable:

Silence threshold
Minimum silence duration
Maximum silence removal

24. DUPLICATE DETECTION

This is one of the most important systems.

Different candidate clips may contain the same idea.

Detect duplicates using:

transcript similarity

semantic similarity

time overlap

sentence overlap

embeddings where available

Example:

Clip A:
"Three things helped me grow..."

Clip B:
"The three things that helped me grow..."

These should not become two separate final Shorts unless the user explicitly chooses aggressive mode.

25. OVERLAP MANAGEMENT

Avoid excessive overlap between final Shorts.

Example:

Short #1:
00:20–00:55

Short #2:
00:35–01:10

These substantially overlap and should normally be merged/rejected.

However, allow limited overlap when two genuinely different moments exist.

Make overlap rules configurable.

26. MAXIMUM USEFUL CLIP ALGORITHM

Implement:

Generate a large candidate pool.

Score all candidates.

Sort by quality.

Remove duplicates.

Remove weak candidates.

Remove excessive overlap.

Re-check context.

Re-check duration.

Re-check audio/video quality.

Add final candidates.

Continue scanning until the entire source is covered.

This should maximize useful coverage rather than simply maximizing quantity.

27. AI-GENERATED TITLE / HOOK

For every final Short generate:

short title

hook

optional description

optional hashtags

Do not generate clickbait that misrepresents the video.

Example:

Title:
"Why Most People Never Finish What They Start"

Hook:
"Most people don't fail because they're lazy..."

Store these separately from the video.

28. SHORT METADATA

Each generated Short should contain:

ID
Project ID
Source video ID
Start time
End time
Duration
Transcript
Title
Hook
Score
Category
Language
Caption status
Render status
Output path
Created date

29. PROCESSING PIPELINE

Processing MUST run as background jobs.

Never keep the browser request waiting for an entire video render.

Pipeline:

JOB 1
Validate source

JOB 2
Download/import

JOB 3
Extract metadata

JOB 4
Extract audio

JOB 5
Transcribe

JOB 6
Analyze transcript

JOB 7
Generate candidates

JOB 8
Score candidates

JOB 9
Remove duplicates

JOB 10
Generate clip plans

JOB 11
Generate captions

JOB 12
Render clips

JOB 13
Validate output

JOB 14
Generate thumbnails

JOB 15
Mark completed

30. JOB QUEUE

Use Redis + Celery or equivalent.

Every job must have:

job ID

project ID

current stage

progress

status

started time

completed time

error message

retry count

Statuses:

QUEUED
PROCESSING
PAUSED
COMPLETED
FAILED
CANCELLED

31. REAL PROGRESS

Do NOT display fake progress.

Progress must correspond to actual processing stages.

Example:

Downloading
██████████████░░ 82%

Transcribing
██████░░░░░░░░░░ 38%

Finding moments
██████████░░░░░░ 61%

Rendering clips
████░░░░░░░░░░░░ 24%

32. RESUMABLE PROCESSING

If rendering clip #17 fails:

DO NOT restart the entire project.

Retry clip #17.

Already completed clips should remain available.

If the server restarts:

Recover queued jobs from the database.

33. CANCEL PROCESSING

Allow:

[Cancel Job]

Cancellation should:

stop queued tasks

safely terminate active subprocesses

clean temporary files

preserve already completed clips

update job status

Do not corrupt the database.

34. VIDEO RENDERING

Use FFmpeg.

Rendering must support:

1080×1920

H.264

AAC

reasonable bitrate

correct pixel format

correct audio sample rate

correct duration

correct rotation metadata

Ensure exported videos work on:

YouTube Shorts

Instagram Reels

TikTok

standard media players

35. AUDIO QUALITY

Preserve good audio.

Support:

loudness normalization

optional noise reduction

silence trimming

clipping prevention

Do not aggressively modify audio by default.

36. CAPTION ENGINE

Generate subtitles using actual transcript timestamps.

Support:

SRT
ASS
embedded captions

For burned-in captions:

Use FFmpeg filters or an equivalent reliable rendering method.

Captions must:

remain inside safe area

avoid covering important faces

avoid bottom UI areas

have sufficient contrast

remain readable on mobile

37. CAPTION WORD HIGHLIGHTING

If enabled:

Current spoken word can be highlighted.

Timing must follow actual word timestamps.

Do not animate randomly.

38. THUMBNAILS

Generate a thumbnail for every Short.

Select a visually strong frame.

If a face is present:

Prefer a clear frame with good facial visibility.

Do not select blurry frames.

39. RESULTS PAGE

After processing:

Show:

"32 Shorts Generated"

Include:

grid/list

preview

title

duration

score

source timestamp

download

regenerate

edit

delete

Provide:

[Download Selected]

[Download All]

[Download ZIP]

40. SHORT PREVIEW

Clicking a Short should open a professional preview modal/page.

Show:

VIDEO PLAYER

Title

Hook

Duration

Score

Source:
00:14:23 → 00:15:04

Actions:

Download
Edit
Regenerate
Delete

41. SIMPLE EDITOR

Allow users to adjust:

start time

end time

title

captions

crop position

caption style

caption position

Then:

[Re-render]

Only re-render the changed Short.

42. SOURCE TIMELINE

Show the selected clip position relative to the original video.

Example:

Original:
00:00 ───────────────────────── 45:22

Selected:
[───────]

This helps users understand where the clip came from.

43. QUALITY CHECK BEFORE EXPORT

Every rendered clip should be validated.

Check:

file exists

file size > 0

valid video stream

valid audio stream where expected

expected duration

resolution

codec

playable by FFprobe

no corrupted output

If validation fails:

Mark render FAILED.

Do not display it as completed.

44. SECURITY

Implement:

authentication

secure password hashing

session/JWT security

authorization checks

upload validation

MIME validation

file extension validation

maximum file size

filename sanitization

path traversal protection

rate limiting

API key protection

secure environment variables

CSRF protection where applicable

CORS configuration

cleanup of temporary files

Never expose:

API keys
database passwords
storage credentials
server paths

to the browser.

45. FILE STORAGE

Use a predictable structure:

storage/
users/
USER_ID/
projects/
PROJECT_ID/
source/
audio/
transcript/
candidates/
renders/
thumbnails/
temp/

Never allow user-provided filenames to directly determine filesystem paths.

46. DATABASE DESIGN

Create proper database models.

At minimum:

User
Project
SourceVideo
Transcript
TranscriptSegment
ClipCandidate
Short
ProcessingJob
RenderJob
Settings

Use foreign keys and indexes.

Do not store huge binary videos directly inside PostgreSQL.

47. ERROR HANDLING

Every major operation needs useful error messages.

Examples:

"Video URL could not be accessed."

"Unsupported video format."

"Audio extraction failed."

"Transcription failed."

"No usable speech was detected."

"AI analysis failed."

"Rendering failed for Short #12."

Do NOT show:

"Something went wrong."

without useful diagnostic information.

48. NO-SPEECH VIDEOS

If the video has little/no speech:

Do not crash.

Offer:

"Speech content is insufficient for transcript-based clipping."

Then optionally use:

scene detection

visual changes

audio peaks

OCR where useful

But do not pretend transcript-based AI analysis succeeded.

49. MULTI-LANGUAGE SUPPORT

Architecture should support multiple languages.

At minimum:

English
Urdu
Arabic
Spanish
French

Do not hard-code English assumptions into the transcript pipeline.

Language detection should determine the transcription language where supported.

50. URL IMPORT

Create a modular URL ingestion service.

Do not hard-code assumptions about one website.

The system should:

validate URL

determine supported source

retrieve permitted media

store local copy

extract metadata

continue normal processing

If a source cannot legally/technically be imported:

show a clear error.

Do not bypass restrictions.

51. COST OPTIMIZATION

This is extremely important.

The system should minimize paid AI usage.

Priority:

Local deterministic processing

Local transcription

Local computer vision

Local/open-source AI

Optional paid AI only where it meaningfully improves quality

Do not send the video itself to an LLM.

Send structured transcript/candidate text instead.

Cache all expensive operations.

Do not re-run transcription unnecessarily.

Do not re-run AI analysis when only caption styling changes.

Do not re-render unchanged clips.

52. MODEL PROVIDER ABSTRACTION

Create an interface such as:

AIProvider

with methods conceptually similar to:

analyzeTranscript()
scoreCandidates()
generateTitle()
generateHook()

Implement a provider system so another model can be added later without rewriting the application.

Possible providers:

Local LLM
OpenAI-compatible API
Other compatible providers

API keys must come from environment variables.

53. PERFORMANCE

Optimize for long videos.

The application should be capable of processing large files without loading the entire video into RAM.

Use:

streaming

temporary files

chunked processing

background workers

caching

parallel rendering where hardware allows

Do not spawn unlimited FFmpeg processes.

Make worker concurrency configurable.

54. GPU SUPPORT

Detect whether GPU acceleration is available.

If available:

use it where appropriate.

If unavailable:

fall back to CPU.

The application must still function without a GPU.

Display:

GPU: Available

or:

GPU: Not detected — CPU mode

55. PROJECT RECOVERY

If the browser closes during processing:

the processing job must continue server-side.

When the user returns:

show current status.

If a worker crashes:

job should be recoverable/retryable.

56. STORAGE CLEANUP

Temporary files must not accumulate forever.

Create cleanup jobs for:

failed temporary renders

abandoned uploads

old intermediate files

Never delete final user outputs automatically without explicit retention rules.

57. SETTINGS

Settings page should include:

AI provider
AI model
Whisper model
GPU/CPU preference
Default clip length
Default quality mode
Caption style
Output resolution
Storage settings
Maximum concurrent renders
Temporary file retention
Language
Theme

58. SYSTEM STATUS

Create a diagnostics page.

Show:

Backend: Online
Database: Connected
Redis: Connected
FFmpeg: Installed
FFprobe: Installed
Whisper: Available
GPU: Available/Unavailable
Storage: Available
AI Provider: Connected/Not Configured

This is extremely useful for professional deployment.

59. UI / UX DESIGN

The website must look like a premium SaaS product.

Design direction:

modern

minimal

professional

dark-first

excellent typography

subtle borders

restrained gradients

clean cards

strong hierarchy

responsive layout

smooth animations

Avoid:

excessive glowing effects

childish UI

unnecessary icons everywhere

huge empty spaces

fake statistics

excessive rounded cards

clutter

cheap template appearance

The design should feel like professional video software.

60. RESPONSIVE DESIGN

Desktop:

optimized for 1440px+.

Laptop:

optimized for 1024–1440px.

Tablet:

usable.

Mobile:

responsive dashboard and project management.

Video processing itself remains server-side.

61. ACCESSIBILITY

Implement:

keyboard navigation

visible focus states

readable contrast

semantic HTML

ARIA where appropriate

accessible form labels

error messages

captions

reduced-motion support

62. DARK/LIGHT MODE

Default:

Dark mode.

Optional:

Light mode.

Do not break contrast in either theme.

63. LOADING STATES

Every asynchronous operation needs a clear state.

Examples:

Uploading...
Analyzing...
Transcribing...
Finding moments...
Removing duplicates...
Rendering...
Finalizing...

Avoid blank screens.

64. EMPTY STATES

Professional empty states.

Example:

"No projects yet.

Upload your first long-form video and let AI discover your best Shorts."

Button:

[Create Project]

65. NOTIFICATIONS

Provide toast notifications for:

project created

upload complete

processing started

processing completed

rendering failed

download ready

project deleted

Avoid excessive notifications.

66. SEARCH / FILTER

Shorts library should allow filtering by:

project

score

duration

date

category

language

status

Search by title/hook.

67. SORTING

Allow:

Highest score
Newest
Longest
Shortest
Most recently rendered

68. BULK OPERATIONS

Allow selecting multiple Shorts.

Actions:

Download
Delete
Regenerate
Change caption style
Export

69. DOWNLOAD ZIP

Generate ZIP files server-side.

Do not load all files into browser memory.

Show ZIP generation progress.

70. EXPORT NAMING

Use clean filenames.

Example:

ProjectName_Short_001.mp4

ProjectName_Short_002.mp4

Avoid:

spaces
illegal filesystem characters
random UUID-only names

Internally use UUIDs.

71. LOGGING

Implement structured logs.

Log:

project ID

job ID

stage

duration

error

worker

Do not log:

passwords
API keys
private credentials

72. TESTING

Create automated tests.

Backend tests:

authentication

upload validation

URL validation

transcript parsing

candidate generation

duplicate detection

job management

authorization

Video tests:

valid output

correct resolution

correct duration

audio presence

caption rendering

Frontend tests:

upload flow

project creation

progress display

result display

download action

73. END-TO-END TEST

Create a small sample video test.

Pipeline:

Upload
↓
Transcribe
↓
Analyze
↓
Generate candidates
↓
Render
↓
Validate
↓
Display
↓
Download

The test should verify the entire workflow.

74. API DESIGN

Create clean REST APIs.

Examples:

POST /api/projects
POST /api/projects/{id}/upload
POST /api/projects/{id}/import-url
POST /api/projects/{id}/process
GET /api/projects/{id}
GET /api/projects/{id}/status
GET /api/projects/{id}/shorts
GET /api/shorts/{id}
PATCH /api/shorts/{id}
POST /api/shorts/{id}/render
DELETE /api/shorts/{id}
POST /api/shorts/bulk-download
GET /api/system/status

Use proper HTTP status codes.

Validate every request.

75. API DOCUMENTATION

FastAPI should automatically expose useful API documentation.

Document:

request bodies
responses
errors
authentication
example requests

76. ENVIRONMENT CONFIGURATION

Create:

.env.example

Never commit actual secrets.

Example categories:

DATABASE_URL
REDIS_URL
SECRET_KEY
AI_PROVIDER
AI_API_KEY
STORAGE_PATH
MAX_UPLOAD_SIZE
WORKER_CONCURRENCY

77. DOCKER

Create:

Dockerfile
docker-compose.yml

Services:

frontend
backend
worker
redis
postgres

Make local setup simple.

Example:

docker compose up --build

78. INSTALLATION DOCUMENTATION

Create a complete README containing:

Requirements

Installation

Environment variables

Docker setup

Local setup

GPU setup

AI provider configuration

Database setup

Running workers

Troubleshooting

Production deployment

Security notes

Do not leave setup undocumented.

79. DEVELOPMENT MODE

Include a development mode that can run without paid APIs.

Use:

local transcription

deterministic candidate generation

optional local AI model

Clearly label where quality is reduced without an AI model.

Do not fake AI functionality.

80. DEMO MODE

If demo mode is implemented, it must be clearly separated from production mode.

Never mix fake data into production dashboards.

81. QUALITY CONTROL DASHBOARD

For each project display:

Candidates found
Candidates rejected
Duplicates removed
Final Shorts
Average score
Average duration
Processing time

Example:

Candidates: 143
Weak clips removed: 31
Duplicates removed: 48
Final Shorts: 64

This helps users understand how the system arrived at the result.

82. CLIP EXPLANATION

For every Short, optionally display:

Why this clip was selected:

"Strong opening statement + complete idea + actionable conclusion + low context dependency."

This explanation should be generated from actual scoring signals.

Do not claim unsupported reasons.

83. AI CONFIDENCE

Do not represent AI scores as objective truth.

Label them:

"AI Quality Score"

not:

"Guaranteed Viral Score"

Never promise virality.

84. NO MANIPULATIVE CLAIMS

Never display:

"Guaranteed viral"
"100% viral"
"Guaranteed millions of views"

Instead use:

"AI Quality Score"
"Hook Strength"
"Content Value"

85. PERFORMANCE TARGET

The system should prioritize:

Fast upload
Fast transcription
Efficient candidate analysis
Parallel rendering
Caching
Minimal redundant work

However, do NOT sacrifice correctness merely to make progress appear faster.

86. FAILURE RECOVERY

If any individual Short fails:

continue processing the remaining Shorts.

At completion:

Example:

32 Shorts requested
29 completed
3 failed

Show:

[Retry Failed]

Do not mark the whole project failed because one clip failed.

87. SOURCE VIDEO PROTECTION

Never modify the original source.

Always maintain an immutable original.

All processing happens on copies/intermediate files.

88. VERSIONING

Store:

pipeline version
AI model version
transcription model
render settings

with each project.

This allows reproducibility.

89. FUTURE-READY ARCHITECTURE

Design the code so future features can be added:

multiple output languages

automatic translation

AI voiceover

B-roll generation

stock footage

branded templates

logo overlays

automatic posting

YouTube scheduling

TikTok scheduling

Instagram scheduling

team accounts

billing

usage limits

Do NOT implement these unless necessary for the initial product.

Build extension points instead.

90. BRANDING

Use a temporary professional name:

"ShortForge AI"

You may structure the code so the name can easily be changed later.

Logo:

Simple text-based logo is acceptable initially.

Do not use copyrighted logos.

91. LANDING PAGE

Create a professional landing page for users who are not logged in.

Hero:

"Turn Long Videos Into Shorts Automatically"

Subheading:

"AI finds the strongest moments, reframes your video, adds captions, and prepares Shorts for publishing."

CTA:

[Start Creating]

Secondary:

[See How It Works]

Sections:

How it works
Features
Workflow
Supported formats
FAQ
CTA

Do not make unsupported claims about performance or virality.

92. SECURITY / PRIVACY

Clearly communicate:

Uploaded videos are processed according to the application's storage/retention settings.

Provide:

Delete Project

When deleted:

database records removed according to policy

source files removed

generated outputs removed

temporary files cleaned

Make deletion explicit and safe.

93. DATABASE CLEANUP

Use scheduled cleanup jobs.

Do not delete active project files.

Do not delete files referenced by active jobs.

Use transaction-safe cleanup.

94. LARGE FILE HANDLING

Do not assume a 500 MB file is the largest possible input.

Make maximum upload size configurable.

Use streaming upload.

Show meaningful error if the limit is exceeded.

95. CONCURRENT USERS

Architecture should avoid global shared temporary filenames.

Every project/job must have isolated working directories.

Two users processing videos simultaneously must never interfere with each other.

96. RENDER CONCURRENCY

Do not render 100 videos simultaneously.

Use worker limits.

Allow configuration:

MAX_RENDER_WORKERS

Respect CPU/GPU resources.

97. AI REQUEST MANAGEMENT

If using external AI:

batch transcript analysis when appropriate

cache responses

retry transient errors

exponential backoff

enforce timeouts

track token/API usage

never retry permanent errors indefinitely

98. MODEL FALLBACK

If the preferred AI provider fails:

If configured, optionally use a fallback provider.

Otherwise:

pause/fail gracefully with a clear message.

Never silently substitute an unrelated model.

99. CLIP EDITING PRIORITY

When creating a clip, prioritize:

Context

Hook

Complete thought

Natural ending

Visual quality

Captions

Composition

Do not sacrifice context just to achieve a short duration.

100. FINAL QUALITY GATE

Before declaring a project complete, verify:

✓ Source imported
✓ Transcript available
✓ Candidates generated
✓ Duplicates removed
✓ Final clips selected
✓ Clips rendered
✓ Videos validated
✓ Captions synchronized
✓ Aspect ratio correct
✓ Audio present
✓ Thumbnails generated
✓ Database records correct
✓ Files accessible
✓ Failed jobs reported
✓ Download works

Only then mark:

PROJECT COMPLETED

101. CODE QUALITY

Write production-quality code.

Requirements:

modular

typed where possible

documented

maintainable

no unnecessary duplication

clear naming

error handling

logging

tests

Do not leave:

TODO
FIXME
"implement later"
placeholder functions
fake API responses
dummy buttons

in production paths.

102. IMPORTANT: DO NOT OVERENGINEER THE FIRST VERSION

Build the complete working MVP first:

Upload / URL
→ Transcription
→ AI analysis
→ Candidate discovery
→ Duplicate removal
→ Smart cropping
→ Captions
→ Rendering
→ Results
→ Download

Then add secondary features.

The application must be usable even if optional advanced features are unavailable.

103. IMPLEMENTATION ORDER

Follow this order:

PHASE 1
Project architecture

PHASE 2
Database

PHASE 3
Authentication

PHASE 4
Upload/import

PHASE 5
Video metadata

PHASE 6
Transcription

PHASE 7
Transcript processing

PHASE 8
Candidate discovery

PHASE 9
AI scoring

PHASE 10
Duplicate detection

PHASE 11
Smart clip boundaries

PHASE 12
9:16 reframing

PHASE 13
Captions

PHASE 14
FFmpeg rendering

PHASE 15
Job queue

PHASE 16
Results UI

PHASE 17
Downloads

PHASE 18
Error recovery

PHASE 19
Testing

PHASE 20
Docker/deployment

PHASE 21
Final QA

104. BEFORE CODING

Before writing code:

Inspect the entire repository.

Determine existing files.

Determine installed dependencies.

Reuse good existing components where appropriate.

Identify missing infrastructure.

Create an implementation plan internally.

Then implement.

Do not unnecessarily overwrite working code.

105. AFTER IMPLEMENTATION

Run:

backend tests

frontend tests

linting

type checking

API validation

database migration checks

FFmpeg checks

end-to-end processing test

Fix all discovered errors.

Do not stop at the first successful page load.

106. FINAL USER TEST

Perform a complete test using a real sample video.

Test:

Upload

Create project

Start processing

Close/reload browser

Return to project

Monitor progress

Wait for processing

Preview Shorts

Edit one Short

Re-render it

Download one

Download multiple

Download ZIP

Delete project

Fix every issue discovered.

107. FINAL OUTPUT TO ME

When finished, provide:

Complete source code

Folder structure

Database migrations

Environment example

Docker configuration

README

Test suite

Setup instructions

Run instructions

Production deployment instructions

Known limitations

List of implemented features

Do not simply tell me what you would build.

BUILD IT.

108. MOST IMPORTANT RULE

The finished application must behave like a real professional AI video editing product.

The user should be able to:

UPLOAD/IMPORT A VIDEO

↓

PRESS "GENERATE SHORTS"

↓

WAIT WHILE THE SERVER PROCESSES IT

↓

SEE REAL PROCESSING PROGRESS

↓

RECEIVE MULTIPLE HIGH-QUALITY SHORTS

↓

PREVIEW THEM

↓

EDIT THEM

↓

DOWNLOAD THEM

without manually performing the technical steps.

Do not create a fake simulation of this workflow.

Implement the actual pipeline.

109. FINAL ACCEPTANCE CRITERIA

The project is NOT complete if:

the upload button does not work

URL importing is fake

transcription is fake

AI analysis is fake

progress is fake

rendering is fake

downloads are fake

captions are unsynchronized

duplicate clips are common

clips randomly cut sentences

face tracking jumps around

the page crashes on large files

one failed clip stops the entire project

API keys are exposed

temporary files accumulate indefinitely

browser refresh loses processing state

the UI contains placeholder buttons

the application requires manually editing source code to operate

The project IS complete only when the full workflow has been tested successfully.

BUILD THE APPLICATION NOW.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/c2bd9190-a85d-4bcc-b5b5-06d93ad17c67).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
