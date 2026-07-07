import React, { useState, useEffect, useCallback } from 'react';
import { Box, Text } from 'ink';
import { Converter } from '@pdf-darker/core';
import type { ConversionResult, ConversionProgress } from '@pdf-darker/shared';
import { ProgressBar } from './components/ProgressBar.js';
import { ResultSummary } from './components/ResultSummary.js';

interface AppProps {
  inputPath: string;
  outputPath: string;
  dpi: number;
  quality: number;
  preserveText: boolean;
}

export function App({ inputPath, outputPath, dpi, quality, preserveText }: AppProps) {
  const [progress, setProgress] = useState<ConversionProgress | null>(null);
  const [result, setResult] = useState<ConversionResult | null>(null);
  const [running, setRunning] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleProgress = useCallback((p: ConversionProgress) => {
    setProgress(p);
  }, []);

  useEffect(() => {
    const converter = new Converter();

    converter
      .convert(
        inputPath,
        outputPath,
        { dpi, quality, preserveText, preserveForms: true, preserveLinks: true },
        handleProgress,
      )
      .then((res) => {
        setResult(res);
        setRunning(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : String(err));
        setRunning(false);
      });
  }, [inputPath, outputPath, dpi, quality, preserveText, handleProgress]);

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold underline>
        pdf-darker — dark mode PDF converter
      </Text>

      <Box marginTop={1} flexDirection="column">
        <Text>
          Input:  <Text dimColor>{inputPath}</Text>
        </Text>
        <Text>
          Output: <Text dimColor>{outputPath}</Text>
        </Text>
      </Box>

      {running && progress && (
        <ProgressBar
          percent={progress.percent}
          page={progress.page}
          totalPages={progress.totalPages}
          phase={progress.phase}
        />
      )}

      {running && !progress && <Text>Starting conversion...</Text>}

      {!running && result && <ResultSummary {...result} />}

      {error && (
        <Box marginTop={1}>
          <Text color="red">Error: {error}</Text>
        </Box>
      )}
    </Box>
  );
}
