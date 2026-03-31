export default function Home() {
  return (
    <main className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <section className="mx-auto flex w-full max-w-6xl flex-1 flex-col justify-center gap-10 px-6 py-24 sm:px-10 lg:px-16">
        <div className="flex flex-col gap-4">
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-zinc-400">
            Sistema ML
          </p>
          <h1 className="max-w-4xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
            RideFare se esta reconstruyendo como un producto de datos para
            inteligencia de precios, analitica y aprendizaje automatico.
          </h1>
          <p className="max-w-3xl text-base leading-8 text-zinc-300 sm:text-lg">
            Esta version ya cuenta con una plataforma de datos reproducible,
            entrenamiento temporal, comparacion de modelos y artefactos listos
            para alimentar la futura experiencia web del producto.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h2 className="text-lg font-semibold text-white">Ingenieria de Datos</h2>
            <p className="mt-3 text-sm leading-7 text-zinc-300">
              El pipeline ya se ejecuta con Polars, DuckDB, dbt y contratos de
              datos para generar marts analiticos y model-ready.
            </p>
          </article>
          <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h2 className="text-lg font-semibold text-white">Modelado ML</h2>
            <p className="mt-3 text-sm leading-7 text-zinc-300">
              El modelado ya salio del notebook y ahora corre con split temporal,
              comparacion de baselines, XGBoost, explicabilidad y exportes estaticos.
            </p>
          </article>
          <article className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h2 className="text-lg font-semibold text-white">Producto Web</h2>
            <p className="mt-3 text-sm leading-7 text-zinc-300">
              La aplicacion publica estara en espanol y se desplegara en Vercel
              como una experiencia de producto, no como un dashboard generico.
            </p>
          </article>
        </div>

        <div className="flex flex-col gap-3 text-sm text-zinc-400 sm:flex-row sm:items-center">
          <span className="rounded-full border border-white/10 px-4 py-2">
            Proximo hito: Producto Web
          </span>
          <span className="rounded-full border border-white/10 px-4 py-2">
            UI publica en espanol
          </span>
          <span className="rounded-full border border-white/10 px-4 py-2">
            Docs tecnicas en ingles
          </span>
        </div>
      </section>
    </main>
  );
}
