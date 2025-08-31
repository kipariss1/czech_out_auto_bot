import path from "path"
import { SQLiteDBhandler } from "./db/SQLiteDBhandler.js"
import { CipherHandler } from './security/cipherHandler.js';

export const smokeTestsDir = path.dirname(path.dirname(__filename));
export const sqliteDBhandler = new SQLiteDBhandler();
export const cipherHandler = new CipherHandler();
