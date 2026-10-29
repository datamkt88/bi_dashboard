# Power BI App Account Setup

*B2C Marketing & OP dashboard: scheduled refresh without Power BI
sign-in pop-ups*

Prepared 29 October 2026 · Tenant: vcintelligence.io

## 1. Purpose

The dashboard refresh used to connect to Power BI through the Claude
desktop app on the laptop, signed in with a personal Power BI login.
When that login token expired or the laptop restarted, a Microsoft
sign-in page popped up in Chrome and the scheduled run could not
continue until someone signed in.

This setup gives the refresh its own app account (a Microsoft Entra
"service principal"). The refresh signs in with the app ID and a secret
and reads the data through the Power BI REST API, so there is no browser
sign-in and no dependency on the laptop.

## 2. Summary of what was set up

| **Item**                     | **Value / setting**                                                                                                                        |
|------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| App registration name        | B2C Dashboard Refresh                                                                                                                      |
| Supported account types      | Single tenant only (vcintelligence.io)                                                                                                     |
| Application (client) ID      | b5857566-ccdd-4ea9-bd76-84e83d13d979                                                                                                       |
| Directory (tenant) ID        | 84bc7d6a-bd5d-4487-b569-950d8f72b7cd                                                                                                       |
| Client secret                | Created 29 Oct 2026, 12-month expiry (renew before ~29 Oct 2027). The secret value is deliberately not recorded in this document.          |
| Security group               | PowerBI-App-Accounts (Security, membership type Assigned), member: B2C Dashboard Refresh                                                   |
| Power BI tenant settings     | "Service principals can call Fabric public APIs" and "Semantic Model Execute Queries REST API", both enabled for PowerBI-App-Accounts only |
| B2C-Player Profile workspace | PowerBI-App-Accounts: Viewer, with Build on Player Profile 360                                                                             |
| B2C-AI workspace             | PowerBI-App-Accounts: Contributor (covers AI Report_Marketing and AI Report_Product)                                                       |
| Claude allowed websites      | login.microsoftonline.com and api.powerbi.com                                                                                              |
| Claude scheduled task        | "Dashboard refresh 10am & 1pm" with Automatically approve turned on                                                                        |

## 3. Step-by-step: Microsoft Entra (entra.microsoft.com)

### 3.1 Create the app registration

1.  Go to **Identity → Applications → App registrations → New
    registration**.

2.  Name: **B2C Dashboard Refresh**.

3.  Supported account types: **Single tenant only – vcintelligence.io**.

4.  Leave Redirect URI empty (no platform selected) and click Register.

5.  On the app's **Overview** page, note the **Application (client) ID**
    and the **Directory (tenant) ID**. No API permissions need to be
    added.

### 3.2 Create the client secret

1.  In the app, open **Certificates & secrets → Client secrets → New
    client secret**.

2.  Enter a description (e.g. "dashboard refresh") and choose a 12-month
    expiry, then click Add.

3.  Copy the **Value** column immediately. Do not use the "Secret ID"
    column; it is only an identifier.

> **Note:** Azure shows the secret value only once. If it is lost,
> delete that secret and create a new one.

### 3.3 Create the security group

1.  Go to **Identity → Groups → All groups → New group**.

2.  Group type: **Security**; name: **PowerBI-App-Accounts**; membership
    type: **Assigned**.

3.  Under Members, add the app **B2C Dashboard Refresh**, then click
    Create. (If the app does not appear in the search, create the group
    first, then use Members → Add members.)

## 4. Step-by-step: Power BI / Fabric admin settings

Tenant settings are under **OneLake catalog → Govern → Configurations →
Tenant settings** (or gear icon → Admin portal → Tenant settings). Use
the search box at the top of the page to find each setting.

1.  Search **Service principals** → open **"Service principals can call
    Fabric public APIs"** → Enabled → Specific security groups → add
    PowerBI-App-Accounts → Apply.

2.  Search **Execute Queries** → open **"Semantic Model Execute Queries
    REST API"** → Enabled → Specific security groups → add
    PowerBI-App-Accounts → Apply.

3.  Allow up to about 15 minutes for tenant setting changes to take
    effect.

## 5. Step-by-step: workspace and model access

The refresh only reads data. It needs the "Build" permission, which in
Power BI means permission to run its own queries against a model; it
does not allow changing the model.

### 5.1 B2C-Player Profile workspace

1.  Workspace → **Manage access → Add people or groups** →
    PowerBI-App-Accounts → role **Viewer**.

2.  Semantic model **Player Profile 360** → … → **Manage permissions** →
    confirm PowerBI-App-Accounts shows **Workspace Viewer, Build**.

### 5.2 B2C-AI workspace

1.  Workspace → **Manage access** → PowerBI-App-Accounts → role
    **Contributor**.

2.  This gives Build on both AI Report_Marketing and AI Report_Product.

> **What happened:** Viewer + Build was tried first on B2C-AI, but the
> app was still refused. After switching the role to Contributor, access
> started working about 10–15 minutes later. Permission changes for app
> accounts are not instant; wait up to an hour before concluding
> something is wrong.

## 6. Step-by-step: Claude settings

### 6.1 Allow the Microsoft websites

1.  Claude → **Settings → Capabilities**. Keep "Use the internet while
    making files" switched on.

2.  Next to **Allowed websites**, click **Manage** and add:

- login.microsoftonline.com (for the app sign-in)

- api.powerbi.com (for reading the data)

### 6.2 Scheduled task approvals

1.  Open the scheduled task **"Dashboard refresh 10am & 1pm"** and turn
    on **Automatically approve** so no approval prompt (for example the
    artifact update) can stop a run.

## 7. Verification (29 October 2026)

- The app account signed in successfully and could see the B2C-AI and
  B2C-Player Profile workspaces and all three models.

- All 29 dashboard queries were pulled through the Power BI REST API and
  compared row by row with the same queries pulled through the laptop
  that morning.

- Marketing and Product models: identical, row for row. Player Profile
  model: same structure and rows; only player values that change during
  the day differed, as expected.

> **Status at time of writing:** cloud data pull validated; the
> scheduled task is being switched to the cloud route, with the laptop
> route kept as a fallback if a cloud pull fails.

## 8. Maintenance

### 8.1 Renewing the secret (before it expires)

1.  About 2 weeks before expiry, create a new client secret in the same
    app (Certificates & secrets → New client secret) and copy its Value.

2.  Give the new value to Claude so the refresh switches to it.

3.  Delete the old secret once the next refresh has run successfully.

### 8.2 If the secret may have leaked

- Delete the secret in Entra immediately (it stops working at once),
  create a new one and give it to Claude.

- Check Entra sign-in logs → Service principal sign-ins for unexpected
  use of B2C Dashboard Refresh.

### 8.3 Troubleshooting

| **Symptom**                                                     | **What to check**                                                                                                                                              |
|-----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| "Dataset not found or you do not have the required permissions" | The group lacks Build on that model or the workspace role is missing. Re-check section 5; allow up to an hour after changes.                                   |
| Connection blocked / 403 from proxy                             | The two websites in section 6.1 are not in Claude's allowed websites.                                                                                          |
| Sign-in error from login.microsoftonline.com                    | Secret expired or deleted, or the app ID/tenant ID changed. See 8.1.                                                                                           |
| "More than 15728640 bytes"                                      | A single query answer exceeded Power BI's 15 MB limit. The refresh already splits the large per-customer pulls; a new very large query may need splitting too. |

### 8.4 Why the laptop connector was not used for this

The Power BI connector inside the Claude desktop app only supports the
personal browser sign-in; it rejects an app ID and secret. The app
account is therefore used through the Power BI REST API from Claude's
cloud workspace instead.
