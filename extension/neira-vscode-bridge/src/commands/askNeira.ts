import * as vscode from 'vscode';
import { collectContext } from '../context/contextCollector';
import { askNeiraStream } from '../api/neiraClient';

export function registerAskNeiraCommand(context: vscode.ExtensionContext): void {
  const disposable = vscode.commands.registerCommand('neira.askAboutSelection', () => {
    const payload = collectContext();

    if (!payload) {
      vscode.window.showWarningMessage('Neira: Select some code first.');
      return;
    }

    vscode.window.showInformationMessage('Sent to Neira — check your browser tab.');

    askNeiraStream(payload, {
      onToken: () => {},
      onError: error => vscode.window.showErrorMessage(`Neira error: ${error}`),
    });
  });

  context.subscriptions.push(disposable);
}