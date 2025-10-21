"use client";

type CitationsListProps = {
  items: string[];
};

export function CitationsList({ items }: CitationsListProps) {
  if (!items.length) {
    return (
      <div className="rounded-lg border-2 border-dashed border-border-strong bg-bg-surface px-4 py-3 text-xs text-text-secondary">
        暂无引用来源。
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-2">
      {items.map((url) => (
        <li
          key={url}
          className="flex items-center justify-between rounded-lg border-2 border-border-strong bg-white px-3 py-2 text-xs shadow-[3px_3px_0px_rgba(0,0,0,0.8)]"
        >
          <span className="truncate text-text-secondary">{trimUrl(url)}</span>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[10px] text-accent-blue underline underline-offset-4"
          >
            打开
          </a>
        </li>
      ))}
    </ul>
  );
}

function trimUrl(url: string) {
  try {
    const parsed = new URL(url);
    return `${parsed.hostname}${parsed.pathname}`.replace(/\/$/, "");
  } catch {
    return url;
  }
}
