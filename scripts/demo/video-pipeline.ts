import { assembleVoiceover } from "./assemble-voiceover";
import { buildTimeline } from "./build-timeline";
import { generateBackgroundMusic } from "./generate-background-music";
import { inspectAudioFiles } from "./inspect-audio";
import { recordDemo } from "./record-demo";
import { renderVideo } from "./render-video";
import { validateVideo } from "./validate-video";

async function main(): Promise<void> {
  const captions = process.argv.includes("--captions") && !process.argv.includes("--no-captions");
  inspectAudioFiles();
  buildTimeline();
  await recordDemo();
  assembleVoiceover();
  generateBackgroundMusic();
  renderVideo({ captions });
  validateVideo();
}

void main();
