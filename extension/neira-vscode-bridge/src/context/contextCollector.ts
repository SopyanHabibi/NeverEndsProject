import * as vscode from 'vscode';
import { VscodeAskPayload } from '../types/neiraTypes';

export function collectContext(): VscodeAskPayload | null {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    return null;
  }

  const selection = editor.selection;
  const selectedCode = editor.document.getText(selection);

  if (!selectedCode.trim()) {
    return null;
  }

  const fileName = editor.document.fileName.split(/[\\/]/).pop() || 'Unknown File';
  const projectName = vscode.workspace.name || 'Unknown Project';
  const errorMessage = collectDiagnosticsForSelection(editor, selection);

  // BARU: ambil root folder project yang lagi dibuka di VS Code
  const workspaceFolder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
  const projectRoot = workspaceFolder?.uri.fsPath || '';

  return { projectName, fileName, selectedCode, errorMessage, projectRoot };
}

function collectDiagnosticsForSelection(
  editor: vscode.TextEditor,
  selection: vscode.Selection
): string {
  const diagnostics = vscode.languages.getDiagnostics(editor.document.uri);

  const overlapping = diagnostics.filter(d => d.range.intersection(selection) !== undefined);

  if (overlapping.length === 0) {
    return '';
  }

  return overlapping
    .map(d => `[${vscode.DiagnosticSeverity[d.severity]}] ${d.message}`)
    .join('\n');
}