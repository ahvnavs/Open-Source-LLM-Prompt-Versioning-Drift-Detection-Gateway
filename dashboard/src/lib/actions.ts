'use server';

export async function runPromptTest(name: string, role: string) {
    const GATEWAY_URL = process.env.GATEWAY_URL || 'http://gateway:8080';
    const API_KEY = process.env.ENTERPRISE_API_KEY || '';

    try {
    const response = await fetch(`${GATEWAY_URL}/v1/prompts/execute`, {
        method: 'POST',
        headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        },
        body: JSON.stringify({
        prompt_id: 'auth-system-onboarding-v2',
        variables: { user_name: name, role: role },
        }),
        cache: 'no-store'
    });

    if (!response.ok) {
        const errorData = await response.json();
        return { error: errorData.detail || 'Gateway rejection' };
    }

    const data = await response.json();
    return { success: true, data };

    } catch (error: any) {
    return { error: `Connection Failed: ${error.message}` };
    }
}
