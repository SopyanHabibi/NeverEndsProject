export interface VscodeAskPayload {
  projectName: string;
  fileName: string;
  selectedCode: string;
  errorMessage: string;
  projectRoot: string;
}

export interface NeiraStreamCallbacks {
  onSessionAssigned?: (sessionId: number) => void;
  onToken: (token: string) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}