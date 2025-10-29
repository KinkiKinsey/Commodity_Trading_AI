"use client";

import { Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { ChevronRight, ExternalLink, X } from "lucide-react";
import type { ChainOfThoughtStep, ComplianceStatus } from "@/lib/state/newsStreamStore";
import { CitationsList } from "./CitationsList";

type ChainOfThoughtDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  steps: ChainOfThoughtStep[];
  title?: string;
  publishedAt?: string;
  citations?: string[];
  complianceStatus?: ComplianceStatus;
};

export function ChainOfThoughtDrawer({
  isOpen,
  onClose,
  steps,
  title,
  publishedAt,
  citations = [],
  complianceStatus = "clean"
}: ChainOfThoughtDrawerProps) {
  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog onClose={onClose} className="relative z-[60]">
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm" aria-hidden="true" />
        </Transition.Child>

        <Transition.Child
          as={Fragment}
          enter="transform transition ease-out duration-300"
          enterFrom="translate-x-full"
          enterTo="translate-x-0"
          leave="transform transition ease-in duration-200"
          leaveFrom="translate-x-0"
          leaveTo="translate-x-full"
        >
          <Dialog.Panel className="fixed right-0 top-0 h-full w-full max-w-2xl overflow-y-auto bg-white shadow-[0_0_40px_rgba(0,0,0,0.45)]">
            <header className="sticky top-0 flex items-center justify-between border-b border-border-primary bg-white px-6 py-5">
              <div>
                <Dialog.Title className="text-lg font-semibold text-text-primary">
                  {title ?? "AI 推理链"}
                </Dialog.Title>
                {publishedAt ? (
                  <p className="mt-1 text-xs text-text-tertiary">
                    生成时间：{formatDateTime(publishedAt)}
                  </p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg border border-border-secondary p-2 text-text-secondary transition hover:border-border-primary hover:text-text-primary"
                aria-label="关闭推理抽屉"
              >
                <X size={18} />
              </button>
            </header>

            <div className="space-y-8 px-6 py-8">
              {complianceStatus !== "clean" ? (
                <div className="rounded-lg border border-market-negative/30 bg-market-negative/10 px-4 py-3 text-xs text-market-negative">
                  {complianceStatus === "blocked"
                    ? "因合规限制，本推理链部分内容被隐藏。"
                    : "部分内容依据合规要求做了脱敏处理。"}
                </div>
              ) : null}

              {steps.length === 0 ? (
                <p className="rounded-lg border border-border-secondary bg-background-tertiary/40 px-4 py-6 text-sm text-text-tertiary">
                  当前新闻尚未提供推理链路。
                </p>
              ) : (
                <ol className="space-y-6">
                  {steps.map((step, index) => (
                    <li key={step.id} className="relative rounded-xl border border-border-primary bg-background-tertiary/60 px-5 py-5">
                      {index < steps.length - 1 ? (
                        <div className="absolute left-5 top-[68px] h-[calc(100%-72px)] w-px bg-border-secondary" aria-hidden />
                      ) : null}

                      <div className="flex items-start gap-3">
                        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-bloomberg-orange text-sm font-semibold text-white">
                          {index + 1}
                        </span>

                        <div className="min-w-0 flex-1 space-y-3">
                          <div className="flex items-start justify-between gap-3">
                            <p className="text-sm leading-relaxed text-text-secondary">{step.text}</p>
                            {step.url ? (
                              <a
                                href={ensureHttp(step.url)}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 rounded border border-border-secondary px-2 py-1 text-[11px] text-text-secondary transition hover:border-border-primary hover:text-text-primary"
                              >
                                相关链接
                                <ExternalLink size={12} aria-hidden />
                              </a>
                            ) : null}
                          </div>

                          {step.evidence ? (
                            <div className="flex items-center gap-2 text-xs text-text-tertiary">
                              <ChevronRight size={14} aria-hidden />
                              <span>{step.evidence}</span>
                            </div>
                          ) : null}
                        </div>
                      </div>
                    </li>
                  ))}
                </ol>
              )}

              <CitationsList items={citations} heading="引用来源" />
            </div>
          </Dialog.Panel>
        </Transition.Child>
      </Dialog>
    </Transition>
  );
}

function formatDateTime(value: string): string {
  try {
    return new Intl.DateTimeFormat("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    }).format(new Date(value));
  } catch {
    return value;
  }
}
function ensureHttp(url: string): string {
  return url.startsWith("http") ? url : `https://${url}`;
}

