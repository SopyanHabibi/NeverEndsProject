import * as vscode from 'vscode';
import { collectContext } from '../context/contextCollector';
import { askNeiraStream } from '../api/neiraClient';
import { getNeiraChannel } from '../ui/outputChannel';

export function registerAskNeiraCommand(context: vscode.ExtensionContext): void {
  const disposable = vscode.commands.registerCommand('neira.askAboutSelection', () => {
    const payload = collectContext();

    if (!payload) {
      vscode.window.showWarningMessage('Neira: Select some code first.');
      return;
    }

    const channel = getNeiraChannel();
    channel.clear();
    channel.show(true);
    channel.appendLine(`--- Neira | ${payload.fileName} ---\n`);

    askNeiraStream(payload, {
      onSessionAssigned: sessionId => {
        channel.appendLine(`[session: ${sessionId}]\n`);
      },
      onToken: token => {
        channel.append(token);
      },
      onError: error => {
        channel.appendLine(`\n⚠️ Error: ${error}`);
      },
      onComplete: () => {
        channel.appendLine('\n\n--- done ---');
      }
    });
  });

  context.subscriptions.push(disposable);
}