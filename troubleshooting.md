# Troubleshooting Guide — NovaMind AI Multimodal Chatbot

---

## Quick Diagnostic

Always run this first before investigating manually:

```powershell
# [PowerShell]
python scripts/bedrock_model_access_check.py
```

This checks all 10 environment requirements and tells you exactly what is failing.

---

## AWS Credential Errors

### Error: `NoCredentialsError` or `Unable to locate credentials`

**Cause:** boto3 cannot find your AWS credentials.

**Fix:**
```powershell
# [PowerShell]
aws configure
# Enter your Access Key ID, Secret Access Key, region (us-east-1), format (json)

# Verify it worked:
aws sts get-caller-identity
```

### Error: `ExpiredTokenException`

**Cause:** Your AWS session token has expired (common with temporary credentials or SSO).

**Fix:**
```powershell
# [PowerShell]
aws sts get-caller-identity
# If this fails, re-authenticate:
aws sso login    # if using SSO
# OR
aws configure    # if using access keys — enter fresh keys
```

### Error: `InvalidClientTokenId`

**Cause:** The Access Key ID is wrong or has been deleted.

**Fix:** Go to AWS Console → IAM → Your user → Security credentials → Create new access key. Then run `aws configure` with the new key.

---

## Bedrock Access Errors

### Error: `AccessDeniedException` on Bedrock calls

**Cause:** Either the IAM user/role does not have Bedrock permissions, or Nova Pro model access has not been enabled in the Bedrock console.

**Fix — Step 1: Enable model access**
```
# [AWS Console]
1. Go to https://console.aws.amazon.com/bedrock/
2. Left menu → Model access
3. Find "Amazon Nova Pro" (under Amazon models)
4. Click "Manage model access" → check the box → Save
5. Wait for status: "Access granted"
```

**Fix — Step 2: Verify IAM permissions**
```
# [AWS Console]
1. Go to IAM → Users → your user
2. Add permission: AmazonBedrockFullAccess
   OR create a custom policy with:
   {
     "Effect": "Allow",
     "Action": [
       "bedrock:InvokeModel",
       "bedrock:InvokeModelWithResponseStream",
       "bedrock:ListFoundationModels"
     ],
     "Resource": "*"
   }
```

### Error: `ValidationException: The model is not supported in this region`

**Cause:** Your AWS region does not support Nova Pro directly.

**Fix — Option A:** Change region to us-east-1
```powershell
# [PowerShell]
aws configure set region us-east-1
```

**Fix — Option B:** Use the cross-region inference profile (works from any US region)
```
# In .env or environment:
BEDROCK_MODEL_ID=us.amazon.nova-pro-v1:0
```

The app does this automatically on first `AccessDeniedException` — but if the base model is entirely unavailable in your region, set the inference profile as the default.

---

## Package / Import Errors

### Error: `ModuleNotFoundError: No module named 'services'`

**Cause:** Streamlit is being run from the wrong directory, or the project root is not in `sys.path`.

**Fix:**
```powershell
# [PowerShell] — always run from the project root
cd "E:\GenAi-Project-Udemy\Code_15042025\Chatbot_text_image"
streamlit run mod_chatbot_frontend.py
```

The frontend has a sys.path fix at the top, but the working directory must be the project root.

### Error: `ModuleNotFoundError: No module named 'boto3'`

**Cause:** Virtual environment is not activated or requirements are not installed.

**Fix:**
```powershell
# [PowerShell]
.\.venv\Scripts\Activate.ps1
pip install -r requirements_new.txt
```

### Error: `ModuleNotFoundError: No module named 'pypdf'`

**Cause:** pypdf is listed as optional — it may not be installed.

**Fix:**
```powershell
# [PowerShell]
pip install pypdf>=4.0.0
```

Note: The app works without pypdf — PDFs are still sent to Bedrock for analysis. Only the sidebar text preview is unavailable.

### Error: `ModuleNotFoundError: No module named 'PIL'`

**Cause:** Pillow is not installed.

**Fix:**
```powershell
# [PowerShell]
pip install Pillow>=10.0.0
```

---

## Streamlit Errors

### Error: `StreamlitAPIException: st.chat_input() can only be used inside a Streamlit app`

**Cause:** You ran `mod_chatbot_frontend.py` directly with `python` instead of `streamlit run`.

**Fix:**
```powershell
# [PowerShell] — CORRECT
streamlit run mod_chatbot_frontend.py

# WRONG — do not do this
python mod_chatbot_frontend.py
```

### Error: `Address already in use` or port 8501 busy

**Cause:** Another Streamlit instance is already running.

**Fix:**
```powershell
# [PowerShell] — find and stop the existing process
Get-Process -Name "streamlit" | Stop-Process -Force

# Then restart:
streamlit run mod_chatbot_frontend.py
```

### Warning: `missing ScriptRunContext`

**Cause:** Code is calling Streamlit functions from a background thread or during import.

**This is a warning, not an error** — the app will still work. It's caused by Streamlit's rerun mechanism and can be safely ignored.

---

## File Upload Errors

### Error: `File does not appear to be a valid PDF`

**Cause:** The file has a `.pdf` extension but is not actually a PDF (e.g., it was renamed, or it is corrupted).

**Fix:** Open the file in a PDF viewer to verify it opens correctly. Re-export from the source application if it was generated programmatically.

### Error: `File is too large`

**Cause:** Image > 5 MB or document > 4.5 MB.

**Fix:** Compress the file:
- **Images:** Use a tool like [squoosh.app](https://squoosh.app) or Photoshop to reduce size
- **PDFs:** Use a PDF compressor (Adobe Acrobat, ilovepdf.com) or split into smaller parts

### Error: `Unsupported file type`

**Cause:** The file extension is not in the supported list.

**Fix:** Convert the file to a supported format. Supported types:
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- Documents: `.pdf`, `.txt`, `.md`, `.html`, `.csv`, `.doc`, `.docx`, `.xls`, `.xlsx`

---

## EC2 Deployment Errors

### Cannot connect via SSH

**Cause:** Security group does not have port 22 open, or the .pem file permissions are wrong.

**Fix — Security group:**
```
# [AWS Console]
EC2 → Security Groups → Edit inbound rules → Add rule: SSH, Port 22, My IP
```

**Fix — .pem file permissions (Linux/Mac):**
```bash
# [Linux/Mac terminal]
chmod 400 mlops-key.pem
```

### Browser cannot reach `http://<ip>:8501`

**Cause:** Security group does not have port 8501 open, or Streamlit is not bound to `0.0.0.0`.

**Fix — Security group:**
```
# [AWS Console]
EC2 → Security Groups → Edit inbound rules
Add rule: Custom TCP, Port 8501, Source: 0.0.0.0/0
```

**Fix — Streamlit binding:**
```bash
# [EC2 — Ubuntu] — must include --server.address 0.0.0.0
streamlit run mod_chatbot_frontend.py --server.port 8501 --server.address 0.0.0.0
```

### App crashed after SSH session closed

**Cause:** The Streamlit process was attached to the SSH session and terminated when it closed.

**Fix:** Always run with `nohup`:
```bash
# [EC2 — Ubuntu]
nohup streamlit run mod_chatbot_frontend.py \
  --server.port 8501 --server.address 0.0.0.0 \
  > nohup.out 2>&1 &
```

---

## Model Response Errors

### Error displayed in chat: `[Bedrock error — ThrottlingException]`

**Cause:** Too many requests in a short period.

**Fix:** Wait 10–30 seconds and try again. If persistent, reduce the frequency of requests. Consider requesting a quota increase in AWS Service Quotas.

### Response is cut off mid-sentence

**Cause:** `max_tokens` setting is too low.

**Fix:** Increase Max response tokens in the sidebar slider (try 4096 or 8192).

### Response is too short / too terse

**Cause:** `temperature` is set very low (< 0.3) combined with a "concise" response style.

**Fix:** Increase the temperature slider to 0.5–0.8, or adjust the system prompt to ask for more detail.

---

## Still Stuck?

1. Run `python scripts/bedrock_model_access_check.py` — the output will pinpoint the failing check
2. Check `nohup.out` on EC2 for server-side logs
3. Check the Streamlit terminal output for Python tracebacks
4. Verify your AWS credentials are for the correct account and region
5. Check the AWS Bedrock Console → Model access page — model access must show "Access granted"
