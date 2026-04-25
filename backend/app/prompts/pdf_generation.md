# Requirements Document Extraction

Based on the conversation history provided, extract and structure the software requirements into a JSON document. Your output must be valid JSON only — no preamble, no explanation, no markdown code fences.

Use this exact structure:

{
  "project_name": "Short name for the project (infer from context)",
  "overview": "2-4 sentence executive summary of what the application does and the problem it solves.",
  "stakeholders": [
    {"name": "User type or stakeholder name", "description": "Their role and relationship to the app"}
  ],
  "functional_requirements": [
    {"id": "FR-001", "title": "Short title", "description": "Full description of what the system must do."}
  ],
  "user_stories": [
    {"id": "US-001", "as_a": "type of user", "i_want": "capability or action", "so_that": "benefit or outcome"}
  ],
  "non_functional_requirements": [
    {"category": "Performance|Security|Usability|Reliability|Scalability|Compliance", "description": "Specific requirement"}
  ],
  "constraints": [
    "Constraint or assumption stated or implied during the conversation"
  ],
  "open_questions": [
    "Things the user was unsure about or explicitly left for later decision"
  ],
  "tech_stack_suggestions": {
    "rationale": "Brief explanation of recommendations based on the described requirements.",
    "frontend": "Recommended frontend framework/technology and why",
    "backend": "Recommended backend technology and why",
    "database": "Recommended database and why",
    "hosting": "Recommended hosting/infrastructure approach",
    "other": ["Any other relevant tools or services"]
  }
}

Extract only what was actually discussed. Use empty arrays for sections where nothing was covered. Do not invent requirements not present in the conversation.
