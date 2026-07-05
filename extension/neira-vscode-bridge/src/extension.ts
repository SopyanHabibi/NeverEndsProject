import * as vscode from 'vscode';
import { registerAskNeiraCommand } from './commands/askNeira';

export function activate(context: vscode.ExtensionContext) {
  registerAskNeiraCommand(context);
}

export function deactivate() {}