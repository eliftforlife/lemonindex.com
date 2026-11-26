// lemon-store entry. The offer engine (engine.js) is private and gitignored: build_content.py copies it in from the private checklist
// folder before a deploy. Without it the bundle fails to build, so a checklist can never ship without its answer screen.
import { handler, setEngine } from './store_lib.js';
import { offer } from './engine.js';
setEngine(offer);
export default handler;
