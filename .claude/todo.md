- Fetch local docs
    [x] Claude Code 2.0
    [x] Astral UV
    [x] FastMCP
- [x] Set up ResumeAgent as HTTP accessible MCP server
- Choose local DB
    Supabase Cloud
        Pros:
            Simplest to set up
        Cons:
            Free tier requires it to be constantly active
    Supabase Local
        Pros:
            Full control
        Cons: 
            Docker compose configuration
    SQLite
        Pros:
            Easy to move a single DB file
            View directly in VSCode
        Cons:
            No vector store?
- Design DB structure
    User details
    Resume details
        Base/original resume
        Tailored resume (linked to job application)
    Career history
    Hobbies
    Job listing details
- Add MCP servers:
    [x] Context7 
    [ ] Database (Supabase Cloud? Supabase local?)
    [ ] Playwright
- Design agent flow using the DB as a normalised knowledge repo
- Customise Docker port
- Docker deploy locally