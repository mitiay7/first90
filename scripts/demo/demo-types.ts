export type AudioFileInspection = {
  index: number;
  fileName: string;
  relativePath: string;
  durationSeconds: number;
  durationMs: number;
  codec: string;
  sampleRate: number;
  channels: number;
  bitRate: number | null;
  sizeBytes: number;
};

export type AudioInspection = {
  version: 1;
  audioFiles: AudioFileInspection[];
  totalNarrationDurationMs: number;
};

export type DemoTimelineScene = {
  id: string;
  audioFile: string;
  description: string;
  execute: string;
  audioDurationMs: number;
  contentDurationMs: number;
  startMs: number;
  audioStartMs: number;
  audioEndMs: number;
  endMs: number;
  leadInMs: number;
  trailingHoldMs: number;
};

export type DemoTimeline = {
  version: 1;
  competitionLimitMs: number;
  totalDurationMs: number;
  totalNarrationDurationMs: number;
  totalSilenceAndHoldMs: number;
  scenes: DemoTimelineScene[];
};
