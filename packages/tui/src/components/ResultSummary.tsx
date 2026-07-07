import React from 'react';
import { Box, Text } from 'ink';

interface ResultSummaryProps {
  success: boolean;
  inputPath: string;
  outputPath: string;
  pageCount: number;
  durationMs: number;
  fileSizeBefore: number;
  fileSizeAfter: number;
  error?: string;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function ResultSummary(result: ResultSummaryProps) {
  if (!result.success) {
    return (
      <Box flexDirection="column" marginTop={1} padding={1}>
        <Text color="red" bold>
          Conversion failed
        </Text>
        <Text color="red">{result.error}</Text>
      </Box>
    );
  }

  const ratio =
    result.fileSizeBefore > 0
      ? ((1 - result.fileSizeAfter / result.fileSizeBefore) * 100).toFixed(1)
      : '0.0';

  return (
    <Box flexDirection="column" marginTop={1} padding={1} borderStyle="round">
      <Text color="green" bold>
        Conversion complete
      </Text>
      <Text>
        Input:  <Text dimColor>{result.inputPath}</Text>
      </Text>
      <Text>
        Output: <Text dimColor>{result.outputPath}</Text>
      </Text>
      <Text>
        Pages:  <Text bold>{result.pageCount}</Text>
      </Text>
      <Text>
        Time:   <Text bold>{(result.durationMs / 1000).toFixed(1)}s</Text>
      </Text>
      <Text>
        Size:   <Text bold>{formatBytes(result.fileSizeBefore)}</Text>
        {' → '}
        <Text bold>{formatBytes(result.fileSizeAfter)}</Text>
        <Text dimColor> ({ratio}% reduction)</Text>
      </Text>
    </Box>
  );
}
