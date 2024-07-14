# Web Tools

This module provides commands to fetch information about IP addresses and domains, using the [ipinfo.io](https://ipinfo.io) API and the Linux [whois](https://github.com/rfc1036/whois) package.

## Commands

- `/whois (domain)`: Fetches whois information for a domain, based on the Linux [whois](https://github.com/rfc1036/whois) command.
- `/ip (ip or domain)`: Fetches information about an IP address or domain using the [ipinfo.io](https://ipinfo.io) API.

### Examples

> `/whois google.com`<br>
> Will send a message with the whois information for `google.com`.

> `/ip telegram.org`<br>
> Will send a message with information about the IP address of `telegram.org`.
