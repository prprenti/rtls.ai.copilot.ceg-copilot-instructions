# Intel CAAS MCP Server Builder Skill

**Version:** 2.1 (Generic Edition)
**Date:** February 2026
**Status:** Production-Ready (Validated with real Intel CAAS deployments)

---

## 🎯 Purpose

This skill guides the creation of production-ready MCP servers for Intel APIs, deployable to any Intel CAAS Kubernetes cluster. It incorporates hard-won lessons from real deployments.

**When to Use:** Building MCP servers for Intel internal APIs (IAPM, HSDES, JIRA, etc.) and deploying them to CAAS.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Intel API Portal access (https://api-portal-internal.intel.com/)
- [ ] API credentials (client_id + client_secret) for your target API
- [ ] CAAS cluster access (get your cluster name from your team's CAAS admin)
- [ ] kubectl configured with your cluster credentials
- [ ] podman installed (NOT Docker — Intel registry requires it)
- [ ] Node.js 20+ installed
- [ ] Understanding of the target API (endpoints, auth, data models)
- [ ] Your team's CAAS namespace name
- [ ] Your team's AMR registry project path (e.g., `amr-registry.caas.intel.com/<your-project>/`)
- [ ] Your team's ingress hostname (e.g., `your-app.intel.com`)

---

## 🔧 Configuration Placeholders

Throughout this guide, replace these placeholders with your team's actual values:

| Placeholder | Description | Example |
|---|---|---|
| `<your-namespace>` | Your CAAS Kubernetes namespace | `my-team` |
| `<your-cluster>` | Your CAAS cluster name | `amr-its-compute-cluster` |
| `<your-ingress-hostname>` | Your team's ingress domain | `my-app-dev.intel.com` |
| `<your-registry-project>` | Your AMR registry project path | `amr-registry.caas.intel.com/my-project` |
| `<your-tls-secret>` | Your namespace's TLS cert secret name | `my-team-certs` |
| `<your-registry-username>` | Your AMR registry service account | *(get from your CAAS admin)* |
| `<your-registry-password>` | Your AMR registry credential | *(get from your CAAS admin — NEVER hardcode)* |

---

## 🏗️ Architecture Decision Tree

### Step 1: Choose Authentication Pattern

**Question:** Does the API need to know WHO the user is?

**Answer "NO" → App-Based OAuth**
- Server owns credentials
- One client_id/secret pair stored in Kubernetes Secret
- API sees: "YourApp-MCP-Server"
- Use cases: Public data, catalogs, reference data

**Answer "YES" → User-Based Auth (SSO pass-through)**
- User's SSO id_token passed through
- No server credentials needed
- API sees the individual user identity
- Use cases: User-specific data, permissions vary by user

### Step 2: Choose Transport

**For Intel CAAS Deployment:** Always use HTTP transport
- Reason: Remote access, scalable, stateless
- Never use stdio (local only)

### Step 3: Choose Build Tool

**Always use esbuild, NEVER tsc alone**
- Reason: tsc runs out of memory on large projects
- Build time: ~40ms (esbuild) vs. OOM crash (tsc)
- Lesson learned: tsc with declaration/sourceMap enabled crashes on large TypeScript MCP projects

---

## 🚀 Implementation Steps

### Phase 1: Project Setup (30 minutes)

#### 1.1 Initialize Project

```bash
mkdir your-mcp-server
cd your-mcp-server
npm init -y
```

#### 1.2 Install Dependencies

```bash
# Core dependencies
npm install @modelcontextprotocol/sdk axios zod express

# Dev dependencies
npm install --save-dev typescript @types/node @types/express esbuild
```

**Critical:** Use exact versions that work:
```json
{
  "@modelcontextprotocol/sdk": "^1.0.4",
  "esbuild": "^0.24.0"
}
```

#### 1.3 Configure package.json Scripts

```json
{
  "type": "module",
  "scripts": {
    "build": "esbuild src/index.ts --bundle --outfile=dist/index.js --platform=node --format=esm --target=node20 --external:@modelcontextprotocol/* --external:express --external:axios --external:zod --external:zod-to-json-schema",
    "start": "node dist/index.js",
    "clean": "rm -rf dist",
    "prebuild": "npm run clean"
  }
}
```

**Critical:** Use esbuild with single entry point bundle, NOT multiple files.

#### 1.4 Configure tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "lib": ["ES2022"],
    "moduleResolution": "node",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": false,
    "sourceMap": false
  }
}
```

**Critical:** Set `declaration: false` and `sourceMap: false` to reduce memory usage during build.

---

### Phase 2: Core Server Implementation (2 hours)

#### 2.1 Create src/index.ts (Main Entry Point)

**CRITICAL LESSONS LEARNED:**

1. **Always use allowedHosts** — The MCP SDK validates Host headers by default
2. **Trust proxy headers** — Required when behind nginx ingress
3. **Add health endpoints BEFORE MCP routes** — They need to bypass MCP validation
4. **Manually mount transport handler** — Don't rely on automatic mounting

```typescript
#!/usr/bin/env node
import { randomUUID } from 'node:crypto';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createMcpExpressApp } from '@modelcontextprotocol/sdk/server/express.js';

// Import your tool registration functions
import { registerYourTools } from './tools/yourtools.js';

function createMCPServer(): McpServer {
  const server = new McpServer(
    { name: 'your-mcp-server', version: '1.0.0' },
    { capabilities: { tools: {} } }
  );

  registerYourTools(server);
  return server;
}

async function startHTTPServer(): Promise<void> {
  const port = parseInt(process.env.PORT || '3000');

  const server = createMCPServer();
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => randomUUID(),
  });

  await server.connect(transport);

  // ⚠️ CRITICAL: Add allowedHosts to prevent "Invalid Host" errors
  const app = createMcpExpressApp({
    host: '0.0.0.0',
    allowedHosts: [
      'localhost',
      '<your-ingress-hostname>',                        // ← Your ingress hostname
      'your-service.<your-namespace>.svc.cluster.local', // ← Kubernetes service FQDN
      'your-service',                                    // ← Short service name
    ]
  });

  // ⚠️ CRITICAL: Trust proxy (required behind nginx ingress on CAAS)
  app.set('trust proxy', true);

  // ⚠️ CRITICAL: Add health check BEFORE MCP routes
  app.get('/health', (_req, res) => {
    res.json({
      status: 'healthy',
      service: 'your-mcp-server',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
    });
  });

  app.get('/', (_req, res) => {
    res.json({
      name: 'your-mcp-server',
      version: '1.0.0',
      endpoints: { health: '/health', mcp: '/mcp' },
    });
  });

  // ⚠️ CRITICAL: Manually mount MCP handler
  app.post('/mcp', (req, res) => {
    transport.handleRequest(req, res, req.body);
  });

  app.listen(port, () => {
    console.error(`Server listening on port ${port}`);
    console.error(`Health: http://localhost:${port}/health`);
    console.error(`MCP: http://localhost:${port}/mcp`);
  });
}

// Start server
const transport = process.env.TRANSPORT || 'http';
if (transport === 'http') {
  startHTTPServer().catch(console.error);
} else {
  console.error('Only HTTP transport is supported for Intel CAAS deployment');
  process.exit(1);
}
```

#### 2.2 Create API Client (src/services/api-client.ts)

**App-Based OAuth Pattern:**

```typescript
import axios, { AxiosInstance } from 'axios';

interface OAuthCredentials {
  clientId: string;
  clientSecret: string;
}

interface CachedToken {
  token: string;
  expiresAt: number;
}

export class APIClient {
  private tokenCache: Map<string, CachedToken> = new Map();
  private axiosInstance: AxiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  async getToken(credentials: OAuthCredentials): Promise<string> {
    const cacheKey = credentials.clientId;
    const cached = this.tokenCache.get(cacheKey);

    if (cached && cached.expiresAt > Date.now()) {
      return cached.token;
    }

    // Intel uses Azure AD (Entra ID) for OAuth
    const response = await axios.post(
      'https://login.microsoftonline.com/intel.onmicrosoft.com/oauth2/v2.0/token',
      new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: credentials.clientId,
        client_secret: credentials.clientSecret,
        scope: 'https://intel.onmicrosoft.com/.default',
      }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );

    const token = response.data.access_token;
    const expiresIn = response.data.expires_in || 3600;

    // Cache with 5-minute safety buffer
    this.tokenCache.set(cacheKey, {
      token,
      expiresAt: Date.now() + (expiresIn - 300) * 1000,
    });

    return token;
  }

  async request<T>(
    url: string,
    credentials: OAuthCredentials
  ): Promise<T> {
    const token = await this.getToken(credentials);

    const response = await this.axiosInstance.get<T>(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    return response.data;
  }
}
```

#### 2.3 Create Tool Schemas (src/schemas/input-schemas.ts)

```typescript
import { z } from 'zod';

// Base schema with common fields
const baseToolSchema = z.object({
  client_id: z.string().optional()
    .describe('OAuth client ID (optional, falls back to env var)'),
  client_secret: z.string().optional()
    .describe('OAuth client secret (optional, falls back to env var)'),
  environment: z.enum(['PRODUCTION', 'SANDBOX']).optional().default('PRODUCTION'),
  format: z.enum(['json', 'markdown']).optional().default('json'),
}).strict();

// Example tool schema
export const searchSchema = baseToolSchema.extend({
  query: z.string().min(1).max(500)
    .describe('Search query string'),
  limit: z.number().int().min(1).max(100).optional().default(50)
    .describe('Maximum number of results to return'),
}).strict();
```

#### 2.4 Register Tools (src/tools/yourtools.ts)

**CRITICAL:** Use zodToJsonSchema to convert Zod schemas to JSON Schema format.

```typescript
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { searchSchema } from '../schemas/input-schemas.js';

export function registerYourTools(server: McpServer): void {
  server.registerTool(
    'your_tool_name',
    {
      description: 'Clear description of what this tool does',
      inputSchema: zodToJsonSchema(searchSchema), // ⚠️ CRITICAL: Convert to JSON Schema
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
      },
    },
    async (args: z.infer<typeof searchSchema>) => { // ⚠️ CRITICAL: Type the args
      try {
        const input = searchSchema.parse(args);

        // Your API logic here
        const result = await yourApiCall(input);

        return {
          content: [{
            type: 'text',
            text: JSON.stringify(result, null, 2)
          }]
        };
      } catch (error) {
        return {
          content: [{
            type: 'text',
            text: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
          }],
          isError: true
        };
      }
    }
  );
}
```

---

### Phase 3: Docker Configuration (30 minutes)

#### 3.1 Create Dockerfile

**CRITICAL LESSONS:**
- Use Intel cache registry for base images
- Set Intel proxy environment variables
- Use esbuild (not tsc) in the build
- Run as non-root user (UID 1001)

```dockerfile
# Build stage
FROM cache-registry.caas.intel.com/docker_hub_remote_cache/library/node:20-alpine AS builder

WORKDIR /app

# Intel proxy settings (required for npm install inside container)
ENV HTTP_PROXY=http://proxy-dmz.intel.com:911
ENV HTTPS_PROXY=http://proxy-dmz.intel.com:912
ENV NO_PROXY=localhost,127.0.0.0/8,.intel.com

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install ALL dependencies (including dev for esbuild)
RUN npm ci

# Copy source
COPY src ./src

# Build with esbuild (FAST!)
RUN npm run build

# Production stage
FROM cache-registry.caas.intel.com/docker_hub_remote_cache/library/node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --production && npm cache clean --force

# Copy built code from builder
COPY --from=builder /app/dist ./dist

# Create non-root user
RUN addgroup -g 1001 -S appuser && adduser -S appuser -u 1001

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3000

# Environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV TRANSPORT=http

# Start server
CMD ["node", "dist/index.js"]
```

#### 3.2 Create .dockerignore

```
node_modules
dist
.git
.env
.env.local
*.md
*.yaml
!.caas/*.yaml
```

---

### Phase 4: Kubernetes Deployment (1 hour)

#### 4.1 Create .caas/secret-development.yaml

**⚠️ NEVER commit real secrets to git! Add `.caas/secret-*.yaml` to your .gitignore.**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: your-mcp-oauth-credentials-dev
  namespace: <your-namespace>
type: Opaque
stringData:
  client_id: "your-client-id-here"
  client_secret: "your-client-secret-here"
```

#### 4.2 Create .caas/deployment-development-simple.yaml

**CRITICAL LESSONS:**
- NO health/readiness probes (they can fail behind ingress due to CAAS network policies — test in your namespace first, and only add probes if they work)
- Set `enableServiceLinks: false`
- Use `imagePullPolicy: Always`
- Run as user 1001

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: your-mcp-server-development
  namespace: <your-namespace>
  labels:
    app: your-mcp-server-development
spec:
  replicas: 2
  selector:
    matchLabels:
      app: your-mcp-server-development
  template:
    metadata:
      labels:
        app: your-mcp-server-development
    spec:
      enableServiceLinks: false
      containers:
        - name: your-mcp-server-development
          image: <your-registry-project>/your-mcp-server-app-dev:latest
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 3000
              protocol: TCP
          env:
            - name: NODE_ENV
              value: "production"
            - name: PORT
              value: "3000"
            - name: TRANSPORT
              value: "http"
            - name: YOUR_API_ENVIRONMENT
              value: "SANDBOX"
            - name: YOUR_API_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: your-mcp-oauth-credentials-dev
                  key: client_id
            - name: YOUR_API_CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: your-mcp-oauth-credentials-dev
                  key: client_secret
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          securityContext:
            runAsNonRoot: true
            runAsUser: 1001
            allowPrivilegeEscalation: false
            capabilities:
              drop:
                - ALL
      restartPolicy: Always
      securityContext:
        fsGroup: 1001

---
apiVersion: v1
kind: Service
metadata:
  name: your-mcp-server-development
  namespace: <your-namespace>
spec:
  type: ClusterIP
  selector:
    app: your-mcp-server-development
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 3000
```

#### 4.3 Create .caas/ingress-development.yaml

**CRITICAL:** Use path-based routing with rewrite-target.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/use-regex: 'true'
    nginx.ingress.kubernetes.io/rewrite-target: /$2
  labels:
    app: your-mcp-server-development
  name: your-mcp-server-development
  namespace: <your-namespace>
spec:
  rules:
  - host: <your-ingress-hostname>
    http:
      paths:
      - backend:
          service:
            name: your-mcp-server-development
            port:
              number: 80
        path: /your-mcp(/|$)(.*)
        pathType: ImplementationSpecific
  tls:
  - hosts:
    - <your-ingress-hostname>
    secretName: <your-tls-secret>
```

---

### Phase 5: Build and Deploy (30 minutes)

#### 5.1 Build with Podman (NOT Docker)

**CRITICAL:** Podman must use user-mode networking to reach Intel registries.

```bash
# Ensure podman machine is using user-mode networking
podman machine stop
podman machine rm -f podman-machine-default
podman machine init --user-mode-networking
podman machine start

# Build image
podman build \
  --tls-verify=false \
  --build-arg http_proxy=http://proxy-dmz.intel.com:911 \
  --build-arg https_proxy=http://proxy-dmz.intel.com:912 \
  --build-arg no_proxy=localhost,127.0.0.0/8,.intel.com \
  -t your-mcp-server:dev-latest \
  -f Dockerfile .
```

#### 5.2 Push to AMR Registry

**⚠️ NEVER hardcode registry credentials in scripts or documentation.**

```bash
# Login to registry (use your team's service account credentials)
# Get these from your CAAS admin — do NOT commit them anywhere
podman login amr-registry.caas.intel.com --username <your-registry-username>
# You will be prompted for your password interactively

# Tag images
VERSION="v1.0.0-$(date +%Y%m%d-%H%M%S)"
podman tag localhost/your-mcp-server:dev-latest <your-registry-project>/your-mcp-server-app-dev:$VERSION
podman tag localhost/your-mcp-server:dev-latest <your-registry-project>/your-mcp-server-app-dev:latest

# Push both tags
podman push --tls-verify=false <your-registry-project>/your-mcp-server-app-dev:$VERSION
podman push --tls-verify=false <your-registry-project>/your-mcp-server-app-dev:latest
```

#### 5.3 Deploy to Kubernetes

```bash
# Set kubeconfig (get your cluster kubeconfig from CAAS admin)
export KUBECONFIG="path/to/<your-cluster>.yaml"

# Apply secret (first time only)
kubectl apply -f .caas/secret-development.yaml

# Apply deployment and service
kubectl apply -f .caas/deployment-development-simple.yaml

# Apply ingress
kubectl apply -f .caas/ingress-development.yaml

# Wait for rollout
kubectl rollout status deployment/your-mcp-server-development -n <your-namespace> --timeout=5m

# Verify
kubectl get pods -n <your-namespace> -l app=your-mcp-server-development
```

#### 5.4 Test Deployment

```bash
# Test health endpoint
curl -k https://<your-ingress-hostname>/your-mcp/health

# Expected: {"status":"healthy",...}

# Test root endpoint
curl -k https://<your-ingress-hostname>/your-mcp/

# Expected: {"name":"your-mcp-server","endpoints":{...}}
```

---

## ⚠️ Critical Lessons Learned (From Real CAAS Deployments)

### Issue 1: TypeScript Compilation Out of Memory
**Symptom:** `FATAL ERROR: Ineffective mark-compacts near heap limit`
**Root Cause:** tsc with declaration/sourceMap enabled on large projects
**Solution:** Use esbuild instead, disable declaration/sourceMap
**Prevention:** Always use esbuild for Intel MCP servers

### Issue 2: "Invalid Host" Error from MCP SDK
**Symptom:** `{"jsonrpc":"2.0","error":{"code":-32000,"message":"Invalid Host: ..."}}`
**Root Cause:** MCP SDK's default DNS rebinding protection rejects non-localhost hosts
**Solution:** Add `allowedHosts` array to `createMcpExpressApp()`
**Prevention:** Always include your ingress hostname and K8s service names in allowedHosts

### Issue 3: Health Probes Failing with 403
**Symptom:** Pods in CrashLoopBackOff, probe logs show HTTP 403
**Root Cause:** Some CAAS namespaces have network policies that restrict pod-to-pod communication
**Solution:** Remove health/readiness probes, or work with your CAAS admin to whitelist probe traffic
**Prevention:** Test probes in your namespace before relying on them; omit them if they fail

### Issue 4: Podman DNS Resolution Failures
**Symptom:** `lookup cache-registry.caas.intel.com: Temporary failure in name resolution`
**Root Cause:** Podman machine not using user-mode networking
**Solution:** Reinit podman machine with `--user-mode-networking` flag
**Prevention:** Always init podman with user-mode networking for Intel builds

### Issue 5: Missing index.js in Container
**Symptom:** `Error: Cannot find module '/app/dist/index.js'`
**Root Cause:** esbuild using `src/**/*.ts` creates multiple bundles instead of single file
**Solution:** Use `src/index.ts` as single entry point with `--outfile=dist/index.js`
**Prevention:** Always use single entry point bundle

### Issue 6: .dockerignore Excluding Source Files
**Symptom:** `COPY src ./src` fails with "no such file or directory"
**Root Cause:** .dockerignore had `src/` and `tsconfig.json` excluded
**Solution:** Remove those exclusions from .dockerignore
**Prevention:** Only exclude node_modules, dist, .env, .git

---

## 🎯 Quality Checklist

Before considering your MCP server complete:

**Code Quality:**
- [ ] All tools use zodToJsonSchema for input schemas
- [ ] All tool handlers have typed parameters (`z.infer<typeof schema>`)
- [ ] Error handling returns actionable messages
- [ ] No duplicate code (DRY principle)
- [ ] No console.log (use console.error for server-side logs)

**Configuration:**
- [ ] package.json uses esbuild (not tsc alone)
- [ ] tsconfig.json has declaration:false, sourceMap:false
- [ ] Dockerfile uses Intel cache registry and proxy
- [ ] .gitignore excludes secrets, kubeconfig files, and .env files
- [ ] .env.example provided (no real credentials)

**Kubernetes:**
- [ ] Deployment has NO health probes (unless tested working in your namespace)
- [ ] enableServiceLinks: false set
- [ ] Runs as non-root user (1001)
- [ ] Secret created for OAuth credentials
- [ ] Ingress uses path-based routing with rewrite-target
- [ ] Service name matches deployment selector
- [ ] No hardcoded credentials anywhere in YAML or scripts

**Security:**
- [ ] No passwords, tokens, or secrets in source code
- [ ] No credentials in Dockerfiles or build scripts
- [ ] Registry login uses interactive password prompt (not inline)
- [ ] Secret YAML files are in .gitignore

**Testing:**
- [ ] Health endpoint returns 200 from inside pod
- [ ] Health endpoint returns 200 from ingress URL
- [ ] Root endpoint returns server info
- [ ] MCP endpoint responds to JSON-RPC (may say "not initialized" — that's OK)
- [ ] Pods are Running (1/1 Ready)
- [ ] No CrashLoopBackOff

---

## 📊 Success Metrics

**Deployment Success:**
- Build time: < 1 minute (with esbuild)
- Docker image size: ~300–400 MB
- Pod startup time: < 10 seconds
- Health endpoint response: < 100ms
- Zero deployment failures

**Code Quality:**
- TypeScript: No compilation errors
- Linting: Zero warnings
- Test coverage: > 80% (recommended goal)

---

## 🔄 Maintenance

**Updating Credentials:**
```bash
# Edit secret
kubectl edit secret your-mcp-oauth-credentials-dev -n <your-namespace>

# Or reapply
kubectl apply -f .caas/secret-development.yaml
```

**Deploying New Version:**
```bash
# Build, tag, push (as above)
VERSION="v1.0.1-$(date +%Y%m%d-%H%M%S)"
# ... build and push commands ...

# Update deployment image
kubectl set image deployment/your-mcp-server-development \
  your-mcp-server-development=<your-registry-project>/your-mcp-server-app-dev:$VERSION \
  -n <your-namespace>

# Wait for rollout
kubectl rollout status deployment/your-mcp-server-development -n <your-namespace>
```

**Rollback:**
```bash
kubectl rollout undo deployment/your-mcp-server-development -n <your-namespace>
```

---

## 🎓 References

- **MCP Protocol:** https://modelcontextprotocol.io/
- **Intel API Portal:** https://api-portal-internal.intel.com/
- **CAAS Documentation:** Internal Intel CAAS docs (ask your CAAS admin)
- **MCP TypeScript SDK:** https://github.com/modelcontextprotocol/typescript-sdk

---

## ✅ Validation

This skill has been validated through:
- ✅ Successful MCP server deployment to Intel CAAS
- ✅ Multiple tools working correctly end-to-end
- ✅ Health endpoint accessible from ingress
- ✅ Zero runtime errors in production
- ✅ Pods running stable for 24+ hours

**If you follow this skill exactly, you will avoid the common CAAS deployment pitfalls documented above.**

---

**Last Updated:** February 2026
**Status:** Generic — suitable for any Intel team using CAAS
