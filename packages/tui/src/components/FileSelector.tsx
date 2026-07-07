import React from 'react';
import { Box, Text } from 'ink';
import TextInput from 'ink-text-input';

interface FileSelectorProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function FileSelector({ label, value, onChange, onSubmit }: FileSelectorProps) {
  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text bold>{label}</Text>
      <TextInput value={value} onChange={onChange} onSubmit={onSubmit} />
    </Box>
  );
}
