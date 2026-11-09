# Writing for a cold reader

Write every SSOT file for a reader who arrives knowing nothing about the project. That reader may be the next agent, or a person who delegates the implementation and does not read the code. A document that confuses a new person also misleads an agent.

- **Lead with the situation.** Say who is doing what and why it matters before describing the mechanism. Then give the details: names, paths, and commands. An entry document (the README, or the top of an area) should explain the current path, what the user sees, and the main boundaries on its own; links are for depth, not for assembling the basic picture.
- **Make it delegable.** For anything a reader might hand to an agent, say what result they should see, what evidence would show it, and when to stop and ask.
- **Use plain words.** Prefer the ordinary word to the internal label. The first time you use a project-specific term, explain it in positive terms, enough for this paragraph to make sense. A link to the glossary adds the full definition but does not replace that local explanation. You may explain a term again in context, but do not give it a different meaning. Keep identifiers, enum values, commands, and quoted text exactly as they are, even in a document written in another language.
- **Explain in prose, look up in tables.** Paragraphs carry reasons, causes, and consequences. Use tables for lookups and comparisons. If a cell needs a sentence of reasoning, that reasoning belongs in a paragraph.
- **Be concrete.** One real example ("a retry after a gateway timeout") makes a rule easier to apply than an abstract description does.
- **State the scope the code has.** Write "all", "only", "every", "never", or "always" only when domain evidence supports that scope; otherwise say "by default", "on Linux", "unless X", or name the exception. A statement that is right in the common case but leaves out the condition misleads a task as much as a wrong one.
- **Keep one fact in one place.** Link instead of copying. When you change a fact, search routed owners, `SSOT/`, and the agent instruction files for older statements of it and fix them too.
- **Write in the declared language.** Use the README's `language`.
- **One paragraph, one line.** Do not break a paragraph or a list item across lines to fit a width. Editors and viewers wrap text themselves; a hard break shows up as a short, ragged line, and in Chinese or Japanese it can add a stray space mid-sentence.
- **Make diagrams parse.** In Mermaid diagrams, write comments with Mermaid's own `%%` syntax, never `<!-- -->` inside the fence, because Mermaid rejects HTML comments.

### Checking behavior claims

For each behavior claim this batch adds or broadens, check the wording itself before the structural checker:

1. Read the final changed passages. Copy each new or broader behavior sentence verbatim into scratch or tool input, keeping its input types, conditions and words such as "all" or "only".
2. For human decisions, apply [human-decision evidence](memory-model.md#human-decision-evidence); for creative or research claims, check the canonical text or original sources and state unverified portions. For software behavior, find the code condition that would make that sentence true. Name the value the condition tests. When a guard tests a derived value, name that derived value in the sentence. Being convertible does not make an input satisfy the converted value's condition: a positive input can become zero during integer conversion.
3. For software behavior, choose an input the sentence includes that might fail that condition. Run it and compare the result with the exact sentence, recording the claim, input and outcome together in scratch or tool output. A before/after differential checks preservation; it does not establish a new generalization's truth.
4. Correct or narrow unsupported wording, or state what could not be checked. Carry the checked conditions into the final response too.

Finish when every new or broader claim in the final saved text is matched to domain evidence and readback, or explicitly qualified as unchecked; software behavior claims additionally need their condition and probe result. A later wording change reopens only that sentence. Check this batch's claims, not every unchanged document. Scratch evidence belongs to the task, not a new SSOT ledger.


Length is not the goal in either direction. Write as much as a newcomer needs to understand the point, and nothing that only restates the code.
