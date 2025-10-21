"use client";

import { Fragment } from "react";
import { createPortal } from "react-dom";
import type { ChainOfThoughtStep, ComplianceStatus } from "@/lib/state/newsStreamStore";
import { CitationsList } from "./CitationsList";

type ChainOfThoughtDrawerProps = {
  open: boolean;
  steps: ChainOfThoughtStep[];
  citations: string[];
  complianceStatus: ComplianceStatus;
  onClose: () => void;
};

export function ChainOfThoughtDrawer({ open, steps, citations, complianceStatus, onClose }: ChainOfThoughtDrawerProps) {
  if (!open) return null;

  return createPortal(
    <Fragment>
      <div className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 z-50 max-h-[80vh] rounded-t-[28px] border-2 border-border-strong bg-white p-6 shadow-[0px_-6px_0px_rgba(0,0,0,0.85)] md:left-auto md:right-8 md:w-[440px] md:rounded-[28px]">
        <div className="flex items-center justify-between">
          <div>
            <p className="terminal-text text-[10px] uppercase tracking-[0.3em] text-border-strong">Chain</p>
            <h3 className="mt-2 text-lg font-semibold text-border-strong">AI 推理链</h3>
            <p className="text-[11px] text-text-secondary">事件影响的逐步推导</p>
          </div>
          <button
            className="terminal-text rounded-full border-2 border-border-strong px-4 py-1 text-[10px] uppercase tracking-[0.2em] text-border-strong hover:-translate-y-0.5 hover:shadow-[3px_3px_0px_rgba(0,0,0,0.8)]"
            onClick={onClose}
          >
            关闭
          </button>
        </div>

        {complianceStatus === "masked" ? (
          <p className="mt-3 rounded-lg border border-accent-bear/40 bg-accent-bear/10 px-3 py-2 text-[10px] text-accent-bear">
            部分文本已根据合规要求脱敏，仅展示摘要信息。
          </p>
        ) : null}
        {complianceStatus === "blocked" ? (
          <p className="mt-3 rounded-lg border border-accent-bear/40 bg-accent-bear/10 px-3 py-2 text-[10px] text-accent-bear">
            此推理链已被屏蔽，暂无法展示具体内容。
          </p>
        ) : null}

        <div className="mt-5 space-y-3 overflow-y-auto pr-2 text-xs text-text-secondary">
          {steps.length === 0 ? (
            <p>暂无推理步骤。</p>
          ) : (
            steps.map((step) => (
              <div key={step.id} className="rounded-xl border-2 border-border-strong bg-bg-surface px-3 py-3">
                <div className="terminal-text mb-1 text-[10px] uppercase tracking-[0.2em] text-border-strong">
                  Step {step.step + 1}
                </div>
                <p className="text-sm text-border-strong">{step.text}</p>
                {step.evidence ? (
                  <p className="mt-1 text-[10px] text-text-secondary">Evidence: {step.evidence}</p>
                ) : null}
                {step.url ? (
                  <a
                    href={step.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 inline-block text-[10px] text-accent-blue underline"
                  >
                    查看来源
                  </a>
                ) : null}
              </div>
            ))
          )}
        </div>

        <div className="mt-6">
          <h4 className="terminal-text text-[11px] uppercase tracking-[0.3em] text-border-strong">Citations</h4>
          <div className="mt-2">
            <CitationsList items={citations} />
          </div>
        </div>
      </div>
    </Fragment>,
    document.body
  );
}
