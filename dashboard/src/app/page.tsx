'use client';

import { useState } from 'react';
import { runPromptTest } from '@/lib/actions';

export default function Home() {
  const [name, setName] = useState('Alice');
  const [role, setRole] = useState('Administrator');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleTest = async () => {
    setLoading(true);
    setResult(null);

    // Calls the secure Node.js function over the network
    const res = await runPromptTest(name, role);
    setResult(res);
    setLoading(false);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-950 text-white font-sans">
      <div className="w-full max-w-2xl bg-gray-900 border border-gray-800 rounded-xl p-8 shadow-2xl">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Prompt Execution Playground</h1>
        <p className="text-gray-400 mb-8 text-sm">Testing bounded context: <span className="font-mono text-blue-400">auth-system-onboarding-v2</span></p>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Variable: {`{user_name}`}</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Variable: {`{role}`}</label>
            <input
              type="text"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>

        <button
          onClick={handleTest}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? 'Executing via Gateway...' : 'Execute Prompt (Live LLM Proxy)'}
        </button>

        {result?.error && (
          <div className="mt-6 p-4 bg-red-900/50 border border-red-500 rounded-lg text-red-200">
            <strong>Execution Failed:</strong> {result.error}
          </div>
        )}

        {result?.success && (
          <div className="mt-8 space-y-4">
            <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
              <h3 className="text-xs uppercase text-gray-500 font-bold mb-2">Hydrated Prompt Sent</h3>
              <p className="font-mono text-sm text-green-400">{result.data.executed_prompt}</p>
            </div>

            <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
              <h3 className="text-xs uppercase text-gray-500 font-bold mb-2">Live LLM Response</h3>
              <p className="text-sm text-gray-200 whitespace-pre-wrap">{result.data.llm_response}</p>
            </div>

            <div className="flex gap-4">
              <span className="bg-gray-800 border border-gray-700 px-3 py-1 rounded text-xs text-gray-400">
                Latency: <span className="text-white">{result.data.telemetry.latency_ms}ms</span>
              </span>
              <span className="bg-gray-800 border border-gray-700 px-3 py-1 rounded text-xs text-gray-400">
                Tokens: <span className="text-white">{result.data.telemetry.token_usage}</span>
              </span>
              <span className="bg-gray-800 border border-gray-700 px-3 py-1 rounded text-xs text-gray-400">
                Model: <span className="text-white">{result.data.telemetry.model_used}</span>
              </span>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
