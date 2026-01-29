// Vertex AI Client for Cloudflare Workers
// Implements Service Account Auth using Web Crypto API (No Node.js dependencies)

function pemToArrayBuffer(pem: string): ArrayBuffer {
  const b64Lines = pem.replace(/-----[^-]+-----/g, '').replace(/\s+/g, '');
  const b64Prefix = b64Lines.replace(/-/g, '+').replace(/_/g, '/');
  
  const str = atob(b64Prefix);
  const buf = new ArrayBuffer(str.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < str.length; i++) {
    view[i] = str.charCodeAt(i);
  }
  return buf;
}

function arrayBufferToBase64Url(buffer: ArrayBuffer): string {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

async function signJwt(payload: any, privateKeyPem: string, clientEmail: string): Promise<string> {
  const header = { alg: 'RS256', typ: 'JWT' };
  
  const now = Math.floor(Date.now() / 1000);
  const claim = {
    iss: clientEmail,
    scope: 'https://www.googleapis.com/auth/cloud-platform',
    aud: 'https://oauth2.googleapis.com/token',
    exp: now + 3600,
    iat: now,
    ...payload
  };

  const encodedHeader = arrayBufferToBase64Url(new TextEncoder().encode(JSON.stringify(header)));
  const encodedClaim = arrayBufferToBase64Url(new TextEncoder().encode(JSON.stringify(claim)));
  const data = `${encodedHeader}.${encodedClaim}`;

  // Import Key
  const keyBuffer = pemToArrayBuffer(privateKeyPem);
  const privateKey = await crypto.subtle.importKey(
    'pkcs8',
    keyBuffer,
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5',
    privateKey,
    new TextEncoder().encode(data)
  );

  return `${data}.${arrayBufferToBase64Url(signature)}`;
}

export class VertexAIClient {
  private projectId: string;
  private clientEmail: string;
  private privateKey: string;
  private location: string;
  private accessToken: string | null = null;
  private tokenExp: number = 0;

  constructor(config: { projectId: string; clientEmail: string; privateKey: string; location?: string }) {
    this.projectId = config.projectId;
    this.clientEmail = config.clientEmail;
    this.privateKey = config.privateKey;
    this.location = config.location || 'us-central1';
  }

  private async getAccessToken(): Promise<string> {
    if (this.accessToken && Date.now() < this.tokenExp) {
      return this.accessToken;
    }

    const jwt = await signJwt({}, this.privateKey, this.clientEmail);
    
    const response = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        assertion: jwt
      })
    });

    const data: any = await response.json();
    if (!response.ok) throw new Error(`Auth Failed: ${JSON.stringify(data)}`);

    this.accessToken = data.access_token;
    this.tokenExp = Date.now() + (data.expires_in * 1000) - 60000; // Buffer 1 min
    return this.accessToken!;
  }

  async generateContent(model: string, prompt: string): Promise<string> {
    const token = await this.getAccessToken();
    const endpoint = `https://${this.location}-aiplatform.googleapis.com/v1/projects/${this.projectId}/locations/${this.location}/publishers/google/models/${model}:generateContent`;

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig: {
          temperature: 0.5,
          maxOutputTokens: 2048
        }
      })
    });

    const data: any = await response.json();
    
    if (!response.ok) {
      throw new Error(`Vertex AI Error: ${JSON.stringify(data)}`);
    }

    if (data.candidates && data.candidates[0] && data.candidates[0].content) {
      return data.candidates[0].content.parts[0].text;
    }
    
    throw new Error('No content generated from Vertex AI');
  }
}
