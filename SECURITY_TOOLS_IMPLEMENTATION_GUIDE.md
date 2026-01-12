# Security Assessment Tools Implementation Guide

## 🎯 Quick Reference: Tool Integration Checklist

### Phase 1: Vulnerability Discovery (Enhanced)

| Tool | Status | Priority | Integration Phase | Output Format |
|------|--------|----------|------------------|---------------|
| **whois** | ➕ ADD | High | External Recon | Domain info, expiration, DNS servers |
| **recon-ng** | ➕ ADD | High | External Recon | Subdomains, DNS records, OSINT data |
| **NMAP** | ✅ KEEP | Critical | Network Discovery | Port map, services, OS detection |
| **BGP Mirror** | ➕ ADD | Conditional | Network Discovery | BGP routes, ASN relationships |
| **OpenVAS** | ✅ KEEP | Critical | Vulnerability Scan | CVE list, severity scores |
| **searchsploit** | ➕ ADD | High | Exploit Check | Exploit availability, POC links |
| **HIBP** | ✅ KEEP | Critical | Credential Check | Breach history, compromised accounts |
| **Dehashed** | ⚠️ REVIEW | Optional | Credential Check | Dark web credentials |
| **Threat Intel** | ⚠️ ENHANCE | Medium | Threat Analysis | IOC matches, threat attribution |

### Phase 2: Vulnerability Validation

| Tool | Status | Priority | Integration Phase | Output Format |
|------|--------|----------|------------------|---------------|
| **Metasploit** | ✅ KEEP | Critical | Exploitation | Exploit results, shell access |
| **searchsploit** | ➕ ADD | High | Exploit Source | Exploit modules for Metasploit |
| **Burp Suite** | ✅ KEEP | Critical | Web App Testing | OWASP findings, injection flaws |
| **SQLMap** | ⚠️ MERGE | Low | Web App Testing | SQL injection results |
| **AnyRun** | ✅ KEEP | High | Malware Analysis | Behavioral analysis, IOCs |
| **BloodHound** | ➕ ADD | Conditional | AD Analysis | Attack paths, privilege escalation |

---

## 📊 Findings Display Template

### For Each Tool Finding:

```json
{
  "finding_id": "TOOL-YYYYMMDD-001",
  "tool_name": "NMAP",
  "tool_version": "7.94",
  "severity": "High",
  "cvss_score": 7.5,
  "title": "Open Port 22 (SSH) on Production Server",
  "description": "SSH service detected on port 22 with weak cipher support",
  "affected_systems": ["192.168.1.100", "web-server-01"],
  "exploitability": {
    "status": "Exploitable",
    "exploit_available": true,
    "exploit_complexity": "Low",
    "searchsploit_matches": 3,
    "metasploit_modules": ["auxiliary/scanner/ssh/ssh_login"]
  },
  "business_impact": {
    "data_exposure": "High",
    "system_availability": "Medium",
    "compliance_risk": ["PCI-DSS", "SOC 2"],
    "reputation_risk": "Medium"
  },
  "remediation": {
    "priority": "High",
    "timeline": "7 days",
    "steps": [
      "1. Disable weak SSH ciphers",
      "2. Implement key-based authentication only",
      "3. Restrict SSH access to management network",
      "4. Enable SSH logging and monitoring"
    ],
    "patches": ["N/A - Configuration change"],
    "workarounds": ["Temporary: Restrict source IPs"],
    "verification": "Re-scan with NMAP after changes"
  },
  "roi_metrics": {
    "manual_discovery_time": "4 hours",
    "automated_time": "2 minutes",
    "time_savings": "99.2%",
    "risk_reduction": "High - Prevents unauthorized access",
    "compliance_value": "PCI-DSS Requirement 1.2.1",
    "cost_savings": "$15,000 (estimated breach cost avoided)"
  }
}
```

---

## 💰 ROI Calculation Framework

### Time Savings Calculation:
```
ROI = ((Manual Time - Automated Time) / Automated Time) × 100
Time Savings = Manual Time - Automated Time
Cost Savings = Time Savings × Hourly Rate
```

### Risk Reduction Calculation:
```
Risk Score Before = Sum of all vulnerability CVSS scores
Risk Score After = Sum after remediation
Risk Reduction = ((Before - After) / Before) × 100
```

### Compliance Value:
- Map findings to compliance requirements
- Calculate compliance gap closure percentage
- Estimate audit failure cost avoidance

---

## 🔧 Remediation Recommendation Template

### Standard Remediation Format:

```markdown
## Finding: [Title]

**Severity:** [Critical/High/Medium/Low]
**CVSS Score:** [X.X]
**Affected Systems:** [List]

### Description
[Detailed description of the finding]

### Business Impact
- **Data Exposure Risk:** [High/Medium/Low]
- **System Availability:** [Impact level]
- **Compliance Issues:** [List applicable frameworks]
- **Estimated Breach Cost:** $[Amount]

### Remediation Steps

#### Priority: [Critical/High/Medium/Low]
#### Timeline: [X days/weeks]

1. **Immediate Actions (0-24 hours):**
   - [Action item 1]
   - [Action item 2]

2. **Short-term (1-7 days):**
   - [Action item 1]
   - [Action item 2]

3. **Long-term (1-4 weeks):**
   - [Action item 1]
   - [Action item 2]

### Configuration Changes
```[code block with exact configuration]```

### Patch Information
- **Patch Available:** [Yes/No]
- **Patch Version:** [Version number]
- **Patch URL:** [Link]

### Workarounds
[If available, temporary mitigation steps]

### Verification
1. [Verification step 1]
2. [Verification step 2]
3. Re-scan with [Tool Name] to confirm remediation

### Dependencies
- [Dependency 1]
- [Dependency 2]

### Resource Requirements
- **Time:** [X hours]
- **Skills:** [Required expertise]
- **Access:** [Required permissions]
```

---

## 🛠️ Tool Integration Patterns

### Pattern 1: External Reconnaissance Chain

```python
def run_external_recon(target_domain):
    """
    Chain: whois → recon-ng → NMAP
    """
    results = {
        'whois': whois_lookup(target_domain),
        'recon_ng': recon_ng_scan(target_domain),
        'nmap': nmap_scan(target_domain)
    }
    
    # Cross-reference findings
    findings = correlate_findings(results)
    
    return {
        'findings': findings,
        'roi': calculate_roi(results),
        'remediation': generate_remediation(findings)
    }
```

### Pattern 2: Vulnerability Discovery Chain

```python
def run_vulnerability_discovery(target):
    """
    Chain: OpenVAS → searchsploit → Prioritize
    """
    # Step 1: Vulnerability scan
    openvas_results = openvas_scan(target)
    
    # Step 2: Check exploit availability
    exploit_results = []
    for cve in openvas_results['cves']:
        exploits = searchsploit_search(cve['id'])
        exploit_results.append({
            'cve': cve,
            'exploits_available': len(exploits) > 0,
            'exploits': exploits
        })
    
    # Step 3: Prioritize based on exploitability
    prioritized = prioritize_by_exploitability(exploit_results)
    
    return {
        'findings': prioritized,
        'roi': calculate_vuln_roi(openvas_results, exploit_results),
        'remediation': generate_vuln_remediation(prioritized)
    }
```

### Pattern 3: Exploitation Validation Chain

```python
def run_exploitation_validation(vulnerabilities):
    """
    Chain: searchsploit → Metasploit → Validate
    """
    validated = []
    
    for vuln in vulnerabilities:
        # Get exploit from searchsploit
        exploit = searchsploit_get_exploit(vuln['cve_id'])
        
        if exploit:
            # Attempt exploitation with Metasploit
            result = metasploit_exploit(exploit, vuln['target'])
            
            validated.append({
                'vulnerability': vuln,
                'exploit_available': True,
                'exploitation_result': result,
                'validated': result['success'],
                'impact': result['impact']
            })
    
    return {
        'findings': validated,
        'roi': calculate_validation_roi(validated),
        'remediation': generate_exploitation_remediation(validated)
    }
```

---

## 📋 Implementation Checklist

### Phase 1: Tool Integration

- [ ] **recon-ng Integration**
  - [ ] Install recon-ng framework
  - [ ] Configure API keys (Shodan, VirusTotal, etc.)
  - [ ] Create wrapper class
  - [ ] Implement result parsing
  - [ ] Add to Phase 1 workflow

- [ ] **searchsploit Integration**
  - [ ] Install Exploit-DB database
  - [ ] Create search wrapper
  - [ ] Integrate with OpenVAS results
  - [ ] Add exploit availability to findings
  - [ ] Link to Metasploit modules

- [ ] **whois Integration**
  - [ ] Install whois library
  - [ ] Create domain lookup function
  - [ ] Parse and structure results
  - [ ] Add to external recon phase

- [ ] **BGP Mirror Integration** (Conditional)
  - [ ] Detect BGP/ASN presence
  - [ ] Integrate BGP route analysis
  - [ ] Parse routing data
  - [ ] Add conditional execution

### Phase 2: Findings Enhancement

- [ ] **Findings Database Schema**
  - [ ] Create unified findings table
  - [ ] Add severity, CVSS, exploitability fields
  - [ ] Add business impact fields
  - [ ] Add remediation fields

- [ ] **ROI Calculation Engine**
  - [ ] Implement time savings calculation
  - [ ] Implement risk reduction metrics
  - [ ] Implement compliance value mapping
  - [ ] Implement cost savings estimation

- [ ] **Remediation Generator**
  - [ ] Create remediation template engine
  - [ ] Implement step-by-step generation
  - [ ] Add priority and timeline calculation
  - [ ] Add verification steps

### Phase 3: UI Updates

- [ ] **Findings Display**
  - [ ] Update findings table with new fields
  - [ ] Add severity indicators
  - [ ] Add exploitability badges
  - [ ] Add business impact visualization

- [ ] **ROI Dashboard**
  - [ ] Create ROI metrics display
  - [ ] Add time savings visualization
  - [ ] Add risk reduction charts
  - [ ] Add compliance value indicators

- [ ] **Remediation Panel**
  - [ ] Create remediation recommendation display
  - [ ] Add priority sorting
  - [ ] Add timeline visualization
  - [ ] Add verification checklist

### Phase 4: Reporting

- [ ] **Enhanced Report Generation**
  - [ ] Update report template
  - [ ] Add findings section with all details
  - [ ] Add ROI analysis section
  - [ ] Add remediation roadmap section

- [ ] **Export Formats**
  - [ ] PDF with all sections
  - [ ] CSV for findings
  - [ ] JSON for API integration
  - [ ] Excel with multiple sheets

---

## 🔗 Tool Dependencies

### Required System Packages:
```bash
# Reconnaissance
pip install recon-ng
pip install python-whois
pip install dnspython

# Exploit Database
apt-get install exploitdb  # or equivalent
# searchsploit comes with exploitdb

# BGP Analysis (if needed)
pip install pybgpstream  # or equivalent BGP library
```

### API Keys Required:
- **recon-ng:** Shodan, VirusTotal, Censys (optional but recommended)
- **BGP Mirror:** Route Views API or similar (if using API)
- **Threat Intel:** Various threat intel feeds

---

## 📝 Example Tool Wrapper Implementation

### recon-ng Wrapper Example:

```python
import subprocess
import json
import re

class ReconNGWrapper:
    def __init__(self, workspace_path="/tmp/recon-ng"):
        self.workspace_path = workspace_path
        self.results = {}
    
    def run_recon(self, target_domain):
        """Run comprehensive recon-ng scan"""
        findings = {
            'subdomains': [],
            'dns_records': {},
            'technology_stack': [],
            'email_addresses': [],
            'social_media': {}
        }
        
        # Subdomain enumeration
        findings['subdomains'] = self._enumerate_subdomains(target_domain)
        
        # DNS reconnaissance
        findings['dns_records'] = self._dns_recon(target_domain)
        
        # Technology stack
        findings['technology_stack'] = self._identify_tech_stack(target_domain)
        
        # Email enumeration
        findings['email_addresses'] = self._enumerate_emails(target_domain)
        
        return {
            'findings': findings,
            'roi': self._calculate_roi(findings),
            'remediation': self._generate_remediation(findings)
        }
    
    def _enumerate_subdomains(self, domain):
        """Use recon-ng to enumerate subdomains"""
        # Implementation here
        pass
    
    def _calculate_roi(self, findings):
        """Calculate ROI for recon-ng findings"""
        manual_time = 8  # hours for manual OSINT
        automated_time = 0.5  # hours for automated
        time_savings = ((manual_time - automated_time) / automated_time) * 100
        
        return {
            'time_savings_percent': time_savings,
            'time_saved_hours': manual_time - automated_time,
            'findings_count': len(findings['subdomains']) + len(findings['email_addresses']),
            'risk_reduction': 'High - Identifies exposed attack surface'
        }
    
    def _generate_remediation(self, findings):
        """Generate remediation recommendations"""
        remediation = []
        
        # Subdomain findings
        if findings['subdomains']:
            remediation.append({
                'finding': f"Found {len(findings['subdomains'])} subdomains",
                'severity': 'Medium',
                'recommendation': 'Review and secure all subdomains',
                'steps': [
                    '1. Audit each subdomain for security',
                    '2. Remove unused subdomains',
                    '3. Implement subdomain take-over protection',
                    '4. Monitor for new subdomain registrations'
                ]
            })
        
        return remediation
```

### searchsploit Wrapper Example:

```python
import subprocess
import json

class SearchSploitWrapper:
    def __init__(self):
        self.exploit_db_path = "/usr/share/exploitdb"
    
    def search_cve(self, cve_id):
        """Search for exploits matching a CVE"""
        # Extract CVE number
        cve_num = cve_id.replace('CVE-', '')
        
        # Run searchsploit
        result = subprocess.run(
            ['searchsploit', '-j', '--cve', cve_id],
            capture_output=True,
            text=True
        )
        
        exploits = json.loads(result.stdout)
        
        return {
            'cve_id': cve_id,
            'exploits_found': len(exploits.get('RESULTS_EXPLOIT', [])),
            'exploits': exploits.get('RESULTS_EXPLOIT', []),
            'exploitability': 'High' if len(exploits.get('RESULTS_EXPLOIT', [])) > 0 else 'Low'
        }
    
    def search_vulnerability(self, vulnerability_name):
        """Search for exploits by vulnerability name"""
        result = subprocess.run(
            ['searchsploit', '-j', vulnerability_name],
            capture_output=True,
            text=True
        )
        
        exploits = json.loads(result.stdout)
        
        return exploits.get('RESULTS_EXPLOIT', [])
    
    def get_exploit_path(self, exploit_id):
        """Get full path to exploit file"""
        result = subprocess.run(
            ['searchsploit', '-p', str(exploit_id)],
            capture_output=True,
            text=True
        )
        
        # Parse path from output
        path_match = re.search(r'Path: (.+)', result.stdout)
        if path_match:
            return path_match.group(1)
        return None
```

---

## 🎯 Next Steps

1. **Review** the tool recommendations in `SECURITY_ASSESSMENT_TOOLS_REVIEW.md`
2. **Prioritize** tool additions based on your organization's needs
3. **Implement** tool wrappers following the patterns above
4. **Integrate** tools into the security assessment workflow
5. **Test** tool combinations to ensure compatibility
6. **Update** UI to display findings, ROI, and remediation
7. **Generate** enhanced reports with all three elements

---

## 📚 Additional Resources

- **recon-ng Documentation:** https://github.com/lanmaster53/recon-ng
- **Exploit-DB:** https://www.exploit-db.com/
- **whois RFC:** RFC 3912
- **BGP Route Views:** https://www.routeviews.org/





