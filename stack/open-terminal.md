# Subscription agents in chat

Open WebUI v0.13.3 can show Codex and Claude Code in the chat model picker.
This optional service runs both CLIs in one container for one subscription
owner. The agents share its workspace and require internet access. The NAS
library and local Ollama models run independently.

## Enable the service

1. Generate a random 32-byte key in a password manager. Set
   `OPEN_TERMINAL_API_KEY` in the stack's private `.env` and keep the value for
   the Open WebUI connection.
2. From the directory containing the running stack's `compose.yaml`, start the
   overlay under the same Compose project name you use for the library:

   ```sh
   docker compose -f compose.yaml -f open-terminal.compose.yaml up -d open-terminal
   docker compose -f compose.yaml -f open-terminal.compose.yaml exec open-terminal bash
   ```

3. In that shell, run `codex login --device-auth` for ChatGPT, or `claude`
   and select Claude subscription sign-in. Complete the provider's prompts.
   Codex device login must be enabled on the account. Keep provider API keys
   unset to use plan allowances. The `terminal-home` volume stores the CLI
   logins and workspace across container replacements.
4. In **Admin Settings → Integrations → Open Terminal**, add a server with
   URL `http://open-terminal:8000` and Bearer authentication using the key
   from step 1. Keep the default private access for an admin-owned connection.
   For a non-admin owner, grant access only to that user. Treat the instance
   admins as trusted. Anyone with terminal access can run commands in that home
   and use its signed-in accounts. The service is reachable on the Compose
   network and publishes no host port.
5. Open a saved chat, use the terminal button to select the server, then
   select a discovered Codex or Claude Code model. Send a short prompt to
   confirm the account and model work. For offline library search and
   citations, select the existing local library model.

## Disable the service

Disable the terminal connection in Open WebUI. From the same stack directory,
run `docker compose -f compose.yaml -f open-terminal.compose.yaml stop open-terminal`.
The named volume retains the logins and workspace for the next start.

See the [Open WebUI agent guide](https://docs.openwebui.com/getting-started/quick-start/connect-an-agent/)
and the [pinned Open Terminal deployment guide](https://github.com/open-webui/open-terminal/blob/v0.17.20/docs/deployment.md#coding-agents).
