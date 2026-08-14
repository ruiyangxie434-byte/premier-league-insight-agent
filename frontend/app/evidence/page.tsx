"use client";

import { useEffect, useState } from "react";
import { SiteHeader } from "../../components/system/site-header";
import { getEvidenceCatalog } from "../../services/api";
import type { EvidenceCatalogData } from "../../types/api";

export default function EvidencePage() {
  const [data, setData] = useState<EvidenceCatalogData | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    getEvidenceCatalog(controller.signal).then((response) => setData(response.data)).catch((reason: unknown) => {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "证据目录加载失败");
    });
    return () => controller.abort();
  }, []);
  return <main className="evidence-page"><div className="page-shell evidence-shell">
    <SiteHeader />
    <section className="evidence-hero"><div><p className="eyebrow">DATA LINEAGE · SCOPE · LIMITS</p><h1>每个结论，<span>都能追到证据。</span></h1><p>统一查看项目实际使用的数据快照、覆盖范围、许可与已知限制。这里展示的是可复现的数据边界，不是实时英超数据库。</p></div>
    {data && <dl className="evidence-summary"><div><dt>SOURCES</dt><dd>{data.source_count}</dd><small>独立数据来源</small></div><div><dt>RECORDS</dt><dd>{data.total_records.toLocaleString()}</dd><small>结构化记录</small></div><div><dt>FOCUS</dt><dd>{data.season_focus}</dd><small>主要赛季范围</small></div></dl>}</section>
    {!data && !error && <div className="evidence-state">正在读取后端证据目录…</div>}
    {error && <div className="evidence-state evidence-error"><strong>暂时无法读取证据目录</strong><p>{error}</p></div>}
    {data && <><section className="evidence-grid" aria-label="数据来源目录">{data.sources.map((source, index) => <article className="evidence-card" key={source.id}>
      <div className="evidence-card-topline"><span>0{index + 1}</span><i data-status={source.status}>{source.status === "ready" ? "完整快照" : "有限覆盖"}</i></div>
      <h2>{source.name}</h2><p className="evidence-provider">{source.provider} · {source.coverage}</p><strong className="evidence-count">{source.record_count.toLocaleString()} <small>{source.record_label}</small></strong>
      <dl className="evidence-meta"><div><dt>快照日期</dt><dd>{source.snapshot_date}</dd></div><div><dt>许可/引用</dt><dd>{source.license}</dd></div></dl>
      <div className="evidence-card-section"><h3>驱动模块</h3><ul>{source.powers.map((item) => <li key={item}>{item}</li>)}</ul></div>
      <div className="evidence-card-section limitations"><h3>使用边界</h3><ul>{source.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div>
      <a href={source.source_url} target="_blank" rel="noreferrer">打开原始来源 ↗</a>
    </article>)}</section>
    <section className="evidence-method"><div><p className="eyebrow">GROUNDING PROTOCOL</p><h2>项目如何避免“模型猜数据”</h2></div><ol>{data.methodology.map((item, index) => <li key={item}><span>0{index + 1}</span><p>{item}</p></li>)}</ol><small>目录口径更新于 {data.generated_at}。记录总数用于展示覆盖规模，不代表不同粒度数据可以直接相加分析。</small></section></>}
  </div></main>;
}
