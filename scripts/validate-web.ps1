corepack pnpm --filter web test

if (Test-Path 'apps/web/.next') {
  Remove-Item -Recurse -Force 'apps/web/.next'
}

corepack pnpm --filter web lint
corepack pnpm --filter web exec tsc --noEmit
corepack pnpm --filter web build
