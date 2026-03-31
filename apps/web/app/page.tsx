export default function Home() {
  return (
    <main className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <section className="mx-auto flex w-full max-w-6xl flex-1 flex-col justify-center gap-10 px-6 py-24 sm:px-10 lg:px-16">
        <div className="flex flex-col gap-4">
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-zinc-400">
            Foundation phase
          </p>
          <h1 className="max-w-4xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
            RideFare se está reconstruyendo como un producto de datos para pricing
            intelligence, analítica y machine learning.
          </h1>
          <p className="max-w-3xl text-base leading-8 text-zinc-300 sm:text-lg">
            Esta versión establece la base técnica del proyecto: estructura
            monorepo, paquete Python, app web en Next.js, documentación inicial y
            comandos de validación para las siguientes fases.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h2 className="text-lg font-semibold text-white">Data Engineering</h2>
            <p className="mt-3 text-sm leading-7 text-zinc-300">
              La base del pipeline se moverá a una arquitectura reproducible con
              Polars, DuckDB, dbt y contratos de datos.
            </p>
          </article>
          <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h2 className="text-lg font-semibold text-white">Machine Learning</h2>
            <p className="mt-3 text-sm leading-7 text-zinc-300">
              El modelado saldrá del notebook y pasará a un flujo trazable con
              benchmarks, evaluación temporal y explicabilidad.
            </p>
          </article>
          <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h2 className="text-lg font-semibold text-white">Producto Web</h2>
            <p className="mt-3 text-sm leading-7 text-zinc-300">
              La aplicación pública estará en español y se desplegará en Vercel
              como una experiencia de producto, no como un dashboard genérico.
            </p>
          </article>
        </div>

        <div className="flex flex-col gap-3 text-sm text-zinc-400 sm:flex-row sm:items-center">
          <span className="rounded-full border border-white/10 px-4 py-2">
            Próximo hito: Data Platform
          </span>
          <span className="rounded-full border border-white/10 px-4 py-2">
            UI pública en español
          </span>
          <span className="rounded-full border border-white/10 px-4 py-2">
            Docs técnicas en inglés
          </span>
        </div>
      </section>
    </main>
  );
}
