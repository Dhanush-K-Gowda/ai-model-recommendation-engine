import { useState } from 'react';
import { apiClient } from '../lib/api';
import { Card, CardBody } from '../components/UI/Card';

export default function TestConnection() {
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const testHealth = async () => {
        setLoading(true);
        setResult(null);
        try {
            const response = await apiClient.healthCheck();
            setResult(response);
        } catch (err) {
            setResult({ error: err });
        } finally {
            setLoading(false);
        }
    };

    const testRecommendations = async () => {
        setLoading(true);
        setResult(null);
        try {
            const response = await apiClient.getRecommendations();
            setResult(response);
        } catch (err) {
            setResult({ error: err });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8 animate-fade-in text-text-main pb-20">
            <div>
                <h1 className="text-4xl font-display font-bold">API Connection Test</h1>
                <p className="text-text-muted mt-2">Test if the frontend can connect to the backend API.</p>
            </div>

            <Card>
                <CardBody className="space-y-4">
                    <div className="flex gap-4">
                        <button
                            onClick={testHealth}
                            disabled={loading}
                            className="px-4 py-2 bg-primary text-white rounded-lg hover:opacity-90 disabled:opacity-50"
                        >
                            Test Health Check
                        </button>
                        <button
                            onClick={testRecommendations}
                            disabled={loading}
                            className="px-4 py-2 bg-secondary text-white rounded-lg hover:opacity-90 disabled:opacity-50"
                        >
                            Test Recommendations
                        </button>
                    </div>

                    {loading && <div className="text-text-muted">Loading...</div>}

                    {result && (
                        <div className="mt-4">
                            <h3 className="font-bold mb-2">Response:</h3>
                            <pre className="bg-surface-hover/30 p-4 rounded-lg overflow-auto text-xs">
                                {JSON.stringify(result, null, 2)}
                            </pre>
                        </div>
                    )}
                </CardBody>
            </Card>
        </div>
    );
}
