"use client";

import { useEffect, useState } from "react";

import { APP_VERSION } from "../../lib/product";
import { getApiBaseUrl, getApiHealth } from "../../services/api";
import type { HealthData } from "../../types/api";

type RequestState = "loading" | "success" | "error";

export function BackendStatus() {
  const [state, setState] = useState<RequestState>("loading");
  const [health, setHealth] = useState<HealthData | null>(null);
  const [apiBaseUrl, setApiBaseUrl] = useState(
    "http://localhost:8000/api",
  );

  useEffect(() => {
    const controller = new AbortController();

    async function checkBackend() {
      const resolvedApiBaseUrl = getApiBaseUrl();
      try {
        const response = await getApiHealth(controller.signal);
        setHealth(response.data);
        setApiBaseUrl(resolvedApiBaseUrl);
        setState("success");
      } catch {
        if (!controller.signal.aborted) {
          setApiBaseUrl(resolvedApiBaseUrl);
          setState("error");
        }
      }
    }

    void checkBackend();

    return () => controller.abort();
  }, []);

  const stateCopy = {
    loading: {
      title: "正在检查后端",
      description: "请保持 FastAPI 服务运行。",
    },
    success: {
      title: "后端连接正常",
      description: "数据接口与 SQLite 已准备就绪。",
    },
    error: {
      title: "暂未连接后端",
      description: "请先在 backend 目录启动 Uvicorn。",
    },
  }[state];

  return (
    <aside className="status-panel" aria-live="polite">
      <div className="status-panel-header">
        <h2>开发环境状态</h2>
        <div className="status-lights" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </div>

      <div className="status-body">
        <div className="status-state" data-state={state}>
          <span className="status-dot" aria-hidden="true" />
          <div>
            <strong>{stateCopy.title}</strong>
            <small>{stateCopy.description}</small>
          </div>
        </div>

        <div className="status-details">
          <div className="status-row">
            <span>API 地址</span>
            <code>{apiBaseUrl}</code>
          </div>
          <div className="status-row">
            <span>环境</span>
            <strong>{health?.environment ?? "development"}</strong>
          </div>
          <div className="status-row">
            <span>版本</span>
            <strong>{health?.version ?? APP_VERSION}</strong>
          </div>
        </div>
      </div>
    </aside>
  );
}
