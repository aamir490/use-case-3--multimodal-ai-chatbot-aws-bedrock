# Cleanup & Cost Guide — NovaMind AI Multimodal Chatbot

## 1. Cost Summary

This project uses **Amazon Bedrock only** for AWS charges. There are no always-on infrastructure costs when running locally.

### Amazon Bedrock — Nova Pro Pricing (us-east-1)

| Token type | Price |
|---|---|
| Input tokens | $0.80 per 1 million tokens |
| Output tokens | $3.20 per 1 million tokens |

### Estimated cost per interaction

| Interaction type | Approx. input tokens | Approx. output tokens | Estimated cost |
|---|---|---|---|
| Short text Q&A | ~200 | ~200 | ~$0.0008 |
| Long text Q&A | ~1,000 | ~500 | ~$0.0024 |
| Image analysis | ~500 + image | ~300 | ~$0.002 – $0.010 |
| PDF Q&A (5 pages) | ~3,000 | ~500 | ~$0.004 |
| PDF Q&A (20 pages) | ~10,000 | ~500 | ~$0.010 |

> A full day of active demo usage (100 interactions) would cost approximately **$0.20 – $2.00**.
> There is **no charge when the app is idle** — Bedrock is billed per request only.

### EC2 Costs (if deployed)

| Instance type | Monthly cost (approx.) |
|---|---|
| t2.micro (free tier) | $0 (12 months free tier) |
| t3.micro | ~$8/month |
| t3.small | ~$16/month |

**Stop or terminate EC2 when not in use** to avoid charges.

---

## 2. AWS Free Tier

The following AWS free tier limits apply (12 months from account creation):

| Service | Free tier limit |
|---|---|
| EC2 t2.micro | 750 hours/month |
| Amazon Bedrock | No free tier — pay per token |

---

## 3. Monitoring Your Costs

### Set up a billing alert (highly recommended)

```
# [AWS Console]
1. Go to AWS Billing Console → Budgets
2. Create Budget → Cost budget
3. Set amount: $5 or $10 (your comfort level)
4. Add your email as alert recipient
5. Save
```

### View current Bedrock costs

```
# [AWS Console]
1. Go to AWS Cost Explorer
2. Filter by Service: Amazon Bedrock
3. Group by: Usage type
```

### Check usage via CLI

```powershell
# [PowerShell]
aws ce get-cost-and-usage `
  --time-period Start=2026-08-01,End=2026-08-31 `
  --granularity MONTHLY `
  --metrics BlendedCost `
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Bedrock"]}}'
```

---

## 4. Complete Cleanup Procedure

Follow these steps when you are finished with the project and want to remove all AWS resources.

### Step 1: Stop the EC2 instance (if running)

```
# [AWS Console]
1. Go to EC2 → Instances
2. Select your instance (novabot-server)
3. Instance state → Stop instance
   (Stop keeps the EBS volume but stops compute charges)
   OR
   Instance state → Terminate instance
   (Terminate deletes everything permanently)
```

### Step 2: Terminate the EC2 instance

```
# [AWS Console]
1. EC2 → Instances → Select instance
2. Instance state → Terminate instance
3. Confirm termination
```

### Step 3: Delete the IAM Role

```
# [AWS Console]
1. Go to IAM → Roles
2. Search for: novabot-ec2-role
3. Select → Delete
4. Confirm deletion
```

### Step 4: Delete the Key Pair (optional)

```
# [AWS Console]
1. Go to EC2 → Key Pairs
2. Select your key pair
3. Actions → Delete
```

Also delete the local .pem file from your machine:
```powershell
# [PowerShell]
Remove-Item "E:\path\to\mlops-key.pem"
```

### Step 5: Delete Security Groups (optional)

```
# [AWS Console]
1. Go to EC2 → Security Groups
2. Select the security group created for the chatbot
3. Actions → Delete security groups
   (You cannot delete the default security group)
```

### Step 6: Revoke Bedrock model access (optional)

```
# [AWS Console]
1. Go to Amazon Bedrock → Model access
2. Find Amazon Nova Pro
3. Manage model access → deselect → Save changes
   (This prevents any accidental future charges from that model)
```

### Step 7: Clean up local files

```powershell
# [PowerShell] — remove the virtual environment to free disk space
Remove-Item -Recurse -Force "E:\GenAi-Project-Udemy\Code_15042025\Chatbot_text_image\.venv"
```

---

## 5. What Does NOT Need Cleanup

Since this project does NOT use the following services, there is nothing to clean up for them:

- ❌ S3 buckets (none created)
- ❌ Lambda functions (none created)
- ❌ API Gateway (none created)
- ❌ DynamoDB tables (none created)
- ❌ Cognito user pools (none created)
- ❌ CloudWatch log groups (only created if you explicitly configured logging)
- ❌ VPC (default VPC was used — no custom VPC created)

---

## 6. Quick Teardown Checklist

```
[ ] Stop / terminate EC2 instance
[ ] Delete IAM role: novabot-ec2-role
[ ] Delete key pair (optional)
[ ] Delete security group (optional)
[ ] Set billing alert to catch any unexpected future charges
[ ] Optionally revoke Bedrock model access
[ ] Delete local .venv folder to free disk space
```
