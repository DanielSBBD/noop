# noop
Take MServ's jobs

# Goals

### <u>Infrastructure Discovery Agent</u>

- [MVP] Create a summary of the infrastructure in an account that can be referenced by other agents
- [Stretch] Have an automatic trigger to run this when first deployed
- [Stretch] Invoke this agent on a schedule

### <u>Alert Agent</u>

- [MVP] Create CloudWatch alarms for the infrastructure discovered by the Infrastructure Discovery Agent (Create a alarm creation tool for the agent)
- [Stretch] Analyze past alerts to tweak thresholds and such on existing alarms
- [Dreams] Implement a feedback mechanism for alerts so the agent can tweak them better
- [Dreams] You can ask it to make certain changes

### <u>Investigator Agent</u>

- [MVP] Automatically find the root cause for an alarm and provide a summary on what the issue is and recommended steps to remediate (use a pipeline to pre-program actions like logging the investigation and send an email to the client)
- [Stretch] Allow user to ask about previous investigations
- [Dreams] Implement a feedback mechanism so it knows how to handle certain alerts better

### Remediation Agent

- [Dreams] Fix standard issues and hand over more complex ones to a human agent, called by the investigator agent

### <u>Report Agent</u>

- [MVP] Allow the user to ask it questions about the infrastructure or past alerts etc
- [Stretch] Report generation to show clients
- [Stretch] Frontend to show results
- [Dream] Fully interactive frontend which has info populated by the AI

### Infrastructure Design Agent

- [Dreams] Allow the user to talk to the agent, which will gather requirements from them and then generate an infrastructure diagram/code
- [Dreams] Allow the user to ask for infrastructure and it will deploy it

### Onboarding Agent

- [Dreams] Generate landing zone based on requirement gathering
- [Dreams] Trigger other agents according to the clients needs

# Deliverables

- Cloudformation stack that deploys these agents