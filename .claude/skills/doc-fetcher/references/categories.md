# Library Category Mappings

This reference provides category mappings for organizing library documentation in `ai_docs/`.

## Category Structure

```
ai_docs/
├── frameworks/        # Web and application frameworks
├── databases/         # Database systems and ORMs
├── ai-ml/            # AI, ML, and LLM libraries
├── frontend/         # Frontend libraries and tools
├── backend/          # Backend utilities and tools
├── testing/          # Testing frameworks
├── devops/           # DevOps and infrastructure tools
└── utilities/        # General-purpose utilities
```

## Common Library Mappings

### Frameworks
- Next.js -> `frameworks/nextjs`
- React -> `frameworks/react`
- Vue -> `frameworks/vue`
- Svelte -> `frameworks/svelte`
- Express -> `frameworks/express`
- FastAPI -> `frameworks/fastapi`
- Django -> `frameworks/django`
- Flask -> `frameworks/flask`
- NestJS -> `frameworks/nestjs`

### Databases
- MongoDB -> `databases/mongodb`
- PostgreSQL -> `databases/postgresql`
- MySQL -> `databases/mysql`
- Redis -> `databases/redis`
- Prisma -> `databases/prisma`
- TypeORM -> `databases/typeorm`
- SQLAlchemy -> `databases/sqlalchemy`
- Supabase -> `databases/supabase`

### AI/ML
- LangChain -> `ai-ml/langchain`
- LangGraph -> `ai-ml/langgraph`
- LlamaIndex -> `ai-ml/llamaindex`
- Transformers -> `ai-ml/transformers`
- TensorFlow -> `ai-ml/tensorflow`
- PyTorch -> `ai-ml/pytorch`
- OpenAI -> `ai-ml/openai`
- Anthropic -> `ai-ml/anthropic`

### Frontend
- Tailwind CSS -> `frontend/tailwindcss`
- shadcn/ui -> `frontend/shadcn-ui`
- Material-UI -> `frontend/material-ui`
- Chakra UI -> `frontend/chakra-ui`
- Vite -> `frontend/vite`
- Webpack -> `frontend/webpack`

### Backend
- Node.js -> `backend/nodejs`
- Deno -> `backend/deno`
- Bun -> `backend/bun`

### Testing
- Jest -> `testing/jest`
- Vitest -> `testing/vitest`
- Playwright -> `testing/playwright`
- Cypress -> `testing/cypress`
- pytest -> `testing/pytest`

### DevOps
- Docker -> `devops/docker`
- Kubernetes -> `devops/kubernetes`
- Terraform -> `devops/terraform`
- GitHub Actions -> `devops/github-actions`

### Utilities
- Lodash -> `utilities/lodash`
- Axios -> `utilities/axios`
- date-fns -> `utilities/date-fns`
- Zod -> `utilities/zod`

## Determining Categories

When determining the category for a library not listed above:

1. **Analyze the library description** from Context7's `resolve-library-id` response
2. **Consider the primary use case** - A library can fit multiple categories; choose the most specific
3. **Default to `utilities/`** for general-purpose libraries when unclear
4. **Ask the user** if the category is ambiguous or the library is domain-specific

## Directory Name Normalization

When creating directory names from library names:

1. **Lowercase everything** - `Next.js` -> `nextjs`
2. **Remove special characters** - `shadcn/ui` -> `shadcn-ui`, `@angular/core` -> `angular-core`
3. **Replace spaces with hyphens** - `Material UI` -> `material-ui`
4. **Keep hyphens from original names** - `date-fns` -> `date-fns`
5. **Remove version prefixes** - `/vercel/next.js/v14` -> `nextjs`

## Examples

| Library Name | Context7 ID | Category | Normalized Path |
|--------------|-------------|----------|-----------------|
| Next.js | /vercel/next.js | frameworks | ai_docs/frameworks/nextjs/ |
| LangGraph | /langchain-ai/langgraph | ai-ml | ai_docs/ai-ml/langgraph/ |
| shadcn/ui | /shadcn/ui | frontend | ai_docs/frontend/shadcn-ui/ |
| Playwright | /microsoft/playwright | testing | ai_docs/testing/playwright/ |
| TailwindCSS | /tailwindlabs/tailwindcss | frontend | ai_docs/frontend/tailwindcss/ |
