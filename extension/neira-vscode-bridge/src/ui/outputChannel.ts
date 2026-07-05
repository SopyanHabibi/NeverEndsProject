import * as vscode from 'vscode';

let channel: vscode.OutputChannel | undefined;

export function getNeiraChannel(): vscode.OutputChannel {
  if (!channel) {
    channel = vscode.window.createOutputChannel('Neira');
  }
  return channel;
}