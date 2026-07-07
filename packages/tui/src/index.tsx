#!/usr/bin/env node
import React from 'react';
import { render } from 'ink';
import meow from 'meow';
import { App } from './app.js';

const cli = meow(
  `
  Usage
    $ pdf-darker <input.pdf> [output.pdf]

  Options
    --dpi, -d       Output DPI (default: 300)
    --quality, -q   JPEG quality 1-100 (default: 95)
    --no-text       Disable hidden text layer preservation

  Examples
    $ pdf-darker input.pdf
    $ pdf-darker input.pdf output-dark.pdf --dpi 200
    $ pdf-darker input.pdf --no-text
`,
  {
    importMeta: import.meta,
    flags: {
      dpi: { type: 'number', shortFlag: 'd', default: 300 },
      quality: { type: 'number', shortFlag: 'q', default: 95 },
      text: { type: 'boolean', default: true },
    },
  },
);

const inputPath = cli.input[0];
const outputPath = cli.input[1] || inputPath?.replace(/\.pdf$/i, '-dark.pdf');

if (!inputPath) {
  console.error('Usage: pdf-darker <input.pdf> [output.pdf]');
  process.exit(1);
}

const { waitUntilExit } = render(
  <App
    inputPath={inputPath}
    outputPath={outputPath}
    dpi={cli.flags.dpi}
    quality={cli.flags.quality}
    preserveText={cli.flags.text}
  />,
);

await waitUntilExit();
