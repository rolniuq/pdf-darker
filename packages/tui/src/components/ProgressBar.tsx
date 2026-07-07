import React from 'react';
import { Box, Text } from 'ink';

interface ProgressBarProps {
  percent: number;
  page: number;
  totalPages: number;
  phase: string;
}

export function ProgressBar({ percent, page, totalPages, phase }: ProgressBarProps) {
  const barWidth = 40;
  const filled = Math.round((percent / 100) * barWidth);
  const empty = barWidth - filled;

  return (
    <Box flexDirection="column" marginTop={1}>
      <Text>
        Page {page}/{totalPages} — {phase}
      </Text>
      <Box>
        <Text color="green">{'█'.repeat(filled)}</Text>
        <Text dimColor>{'█'.repeat(Math.max(0, empty))}</Text>
        <Text> {percent}%</Text>
      </Box>
    </Box>
  );
}
