'use client';
export default function ErrorPage({reset}) {
  return <main className="next-state"><h1>Unable to open PayPoint</h1><p>Please try again. Your records have not been changed.</p><button className="button button-primary" onClick={reset}>Try again</button></main>;
}
