# MotionSlate Studio

A CapCut-inspired (not affiliated) responsive browser video editor hosted on the existing `oyunopti.com` domain.

Core implemented features: upload local video; trim range with I/O shortcuts; 9:16, 1:1 and 16:9 framing; text styles and animations; manually timed captions; color presets, brightness and horizontal mirror; audio volume and optional user-provided soundtrack; speed and mute; PNG frame; MediaRecorder export to MP4 when available, otherwise WebM.

## Limitations
Current editor supports one video file per project and manually timed captions. Export occurs in real time, can be sensitive to device and browser capabilities and is not an FFmpeg encoder. Full CapCut features such as multiple media tracks, animated transitions, templates, AI transcription and cloud projects are not included. No automatic ads are inserted.

## Privacy
All user video/audio files remain in the browser. No server-side processing or login.

## Hosting
GitHub Pages with CNAME `oyunopti.com`. Old versions are preserved in GitHub branch history.
