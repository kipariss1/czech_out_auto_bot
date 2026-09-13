import path from "path"
import { PostgresDBHandler } from "./db/PostgresDBHandler"
import { fileURLToPath } from "url";

export const smokeTestsDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
export const testDBHandler = new PostgresDBHandler();
await testDBHandler.connect();
