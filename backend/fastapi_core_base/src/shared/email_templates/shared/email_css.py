"""CSS styles for email templates."""


def get_email_css() -> str:
    """Get the complete CSS stylesheet for email templates."""
    return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #F2F4F6;
        }
        .email-container {
            max-width: 600px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        .header {
            padding: 32px 40px;
            background: linear-gradient(135deg, #d32f2f 0%, #c62828 100%);
            color: #ffffff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .header-title {
            font-size: 22px;
            font-weight: 600;
            margin: 0;
        }
        .content {
            padding: 40px;
            margin-bottom: 20px;
        }
        .info-grid {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 10px 20px;
            margin-bottom: 24px;
            font-size: 14px;
            padding: 20px;
            background-color: #fafafa;
            border-radius: 8px;
        }
        @media only screen and (max-width: 600px) {
            .info-grid {
                grid-template-columns: 1fr;
                gap: 8px;
            }
            .button-group {
                flex-direction: column;
            }
            .button-group a {
                width: 100%;
                text-align: center;
            }
            .progress-steps {
                flex-direction: column;
                gap: 16px;
            }
            .progress-step::after {
                display: none;
            }
            .timeline-item {
                padding-left: 28px;
            }
            .timeline-item::before {
                left: 6px;
            }
            .timeline-item:not(:last-child)::after {
                left: 11px;
            }
            .section-divider {
                margin: 32px 0 24px 0;
            }
        }
        .button-group {
            margin-top: 20px;
            margin-bottom: 0;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: flex-end;
        }
        .button-group a {
            min-width: 160px;
            text-align: center;
        }
        .info-label {
            color: #555;
            font-weight: 500;
            font-size: 13px;
        }
        .info-value {
            color: #1a1a1a;
            font-weight: 500;
            word-break: break-word;
        }
        .info-badge {
            display: inline-block;
            padding: 4px 12px;
            background-color: #fff3e0;
            color: #e65100;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .error-badge-network {
            display: inline-block;
            padding: 5px 14px;
            background-color: #e3f2fd;
            color: #1565c0;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid #90caf9;
        }
        .error-badge-timeout {
            display: inline-block;
            padding: 5px 14px;
            background-color: #fff3e0;
            color: #f57c00;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid #ffb74d;
        }
        .error-badge-validation {
            display: inline-block;
            padding: 5px 14px;
            background-color: #fce4ec;
            color: #c2185b;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid #f48fb1;
        }
        .error-badge-code {
            display: inline-block;
            padding: 5px 14px;
            background-color: #ffebee;
            color: #c62828;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid #ef5350;
        }
        .error-badge-transient {
            display: inline-block;
            padding: 5px 14px;
            background-color: #e8f5e9;
            color: #2e7d32;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid #81c784;
        }
        .error-badge-general {
            display: inline-block;
            padding: 5px 14px;
            background-color: #f5f5f5;
            color: #616161;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid #bdbdbd;
        }
        .severity-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .severity-critical {
            background-color: #ffebee;
            color: #c62828;
            border: 1px solid #ef5350;
        }
        .severity-high {
            background-color: #fff3e0;
            color: #e65100;
            border: 1px solid #ff9800;
        }
        .severity-medium {
            background-color: #e3f2fd;
            color: #1565c0;
            border: 1px solid #2196f3;
        }
        .progress-indicator {
            margin-top: 0;
            margin-bottom: 0;
            padding: 20px;
            background-color: #fafafa;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        .progress-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .progress-title {
            font-size: 13px;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .progress-error-type {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .progress-steps {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }
        .progress-step {
            flex: 1;
            text-align: center;
            font-size: 11px;
            color: #666;
            position: relative;
        }
        .progress-step::after {
            content: '';
            position: absolute;
            top: 12px;
            right: -50%;
            width: 100%;
            height: 2px;
            background-color: #e0e0e0;
            z-index: 0;
        }
        .progress-step:last-child::after {
            display: none;
        }
        .progress-step-icon {
            display: inline-block;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: #e0e0e0;
            color: #999;
            line-height: 24px;
            font-size: 12px;
            margin-bottom: 6px;
            position: relative;
            z-index: 1;
        }
        .progress-step.completed .progress-step-icon {
            background-color: #4caf50;
            color: #fff;
        }
        .progress-step.failed .progress-step-icon {
            background-color: #d32f2f;
            color: #fff;
        }
        .progress-step.pending .progress-step-icon {
            background-color: #e0e0e0;
            color: #999;
        }
        .timeline {
            margin-top: 0;
            margin-bottom: 0;
            padding: 20px;
            background-color: #fafafa;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        .timeline-title {
            font-size: 13px;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 16px;
        }
        .timeline-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 16px;
            position: relative;
            padding-left: 32px;
        }
        .timeline-item:last-child {
            margin-bottom: 0;
        }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: 8px;
            top: 4px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #e0e0e0;
            border: 2px solid #fff;
            z-index: 2;
            box-sizing: border-box;
        }
        .timeline-item.completed::before {
            background-color: #4caf50;
        }
        .timeline-item.failed::before {
            background-color: #d32f2f;
        }
        .timeline-item.pending::before {
            background-color: #ff9800;
        }
        .timeline-item:not(:last-child)::after {
            content: '';
            position: absolute;
            left: 13px;
            top: 16px;
            width: 2px;
            height: calc(100% + 4px);
            background-color: #e0e0e0;
            z-index: 1;
            margin-left: 0;
        }
        .timeline-item.completed:not(:last-child)::after {
            background-color: #4caf50;
        }
        @media only screen and (max-width: 600px) {
            .timeline-item:not(:last-child)::after {
                display: none;
            }
        }
        .timeline-content {
            flex: 1;
            padding-top: 0;
        }
        .timeline-stage {
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-bottom: 4px;
            line-height: 1.4;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }
        .timeline-time {
            font-size: 12px;
            color: #666;
            line-height: 1.5;
        }
        .timeline-status {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        }
        .timeline-status.completed {
            background-color: #e8f5e9;
            color: #2e7d32;
        }
        .timeline-status.failed {
            background-color: #ffebee;
            color: #c62828;
        }
        .timeline-status.pending {
            background-color: #fff3e0;
            color: #f57c00;
        }
        .error-section {
            margin-top: 0;
            margin-bottom: 0;
            padding: 22px;
            background: linear-gradient(to right, #fdf2f2 0%, #ffffff 100%);
            border-left: 5px solid #dc2626;
            border-radius: 8px;
        }
        .error-label {
            font-size: 12px;
            font-weight: 700;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 16px;
            padding: 10px 12px;
            background: #fef2f2;
            border-radius: 6px;
        }
        .error-message {
            color: #991b1b;
            font-size: 14px;
            line-height: 1.6;
            font-weight: 500;
        }
        .section-divider {
            margin: 32px 0 24px 0;
            height: 1px;
            background: linear-gradient(to right, transparent, #e0e0e0 20%, #e0e0e0 80%, transparent);
            border: none;
        }
        .traceback-section {
            margin-top: 0;
            padding: 18px;
            background-color: #fafafa;
            border-left: 4px solid #757575;
            border-radius: 8px;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            max-height: 300px;
            overflow-y: auto;
        }
        .traceback-label {
            font-size: 12px;
            font-weight: 700;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .traceback-content {
            font-size: 11px;
            line-height: 1.8;
            color: #424242;
            overflow-x: auto;
        }
        .traceback-line {
            margin-bottom: 3px;
            word-break: break-all;
        }
        .indent-1 {
            padding-left: 20px;
            color: #616161;
        }
        .indent-2 {
            padding-left: 40px;
            color: #616161;
        }
        .traceback-error {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #bdbdbd;
            color: #d32f2f;
            font-weight: 700;
        }
        .traceback-scroll {
            scrollbar-color: #FF3131 #121212;
            scrollbar-width: thin;
        }
        .traceback-scroll::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        .traceback-scroll::-webkit-scrollbar-track {
            background: #121212;
            border-radius: 10px;
        }
        .traceback-scroll::-webkit-scrollbar-thumb {
            background: #FF3131;
            border-radius: 10px;
            border: 2px solid #121212;
            min-height: 40px;
        }
        .traceback-scroll::-webkit-scrollbar-thumb:hover {
            background: #ff5252;
        }
        .error-details-scroll {
            scrollbar-color: #dc2626 #fecaca;
            scrollbar-width: auto;
        }
        .error-details-scroll::-webkit-scrollbar {
            width: 12px;
            height: 12px;
        }
        .error-details-scroll::-webkit-scrollbar-track {
            background: #fecaca !important;
            border-radius: 6px;
        }
        .error-details-scroll::-webkit-scrollbar-thumb {
            background: #dc2626 !important;
            border: 2px solid #fecaca;
            border-radius: 6px;
            min-height: 40px;
        }
        .error-details-scroll::-webkit-scrollbar-thumb:hover {
            background: #b91c1c !important;
        }
        /* Success status card watermark: never intercepts clicks or text selection */
        .success-card-watermark {
            pointer-events: none;
            z-index: 0;
        }
        /* Failure status card watermark */
        .failure-card-watermark {
            pointer-events: none;
            z-index: 0;
        }
        .footer {
            padding: 28px 40px;
            border-top: 1px solid #E0E0E0;
            font-size: 11px;
            color: #666;
            text-align: center;
            background: #F1F3F5;
            margin-top: 20px;
        }
        .footer-content {
            max-width: 500px;
            margin: 0 auto;
        }
        .footer-logo {
            margin-bottom: 12px;
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }
        .footer-reference {
            margin-bottom: 12px;
            padding: 8px 12px;
            background-color: #fff;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 10px;
            color: #666;
        }
        .footer-reference strong {
            color: #333;
        }
        .footer-links {
            margin: 12px 0;
            padding-top: 12px;
            border-top: 1px solid #e0e0e0;
        }
        .footer-links a {
            color: #1976d2;
            text-decoration: none;
            margin: 0 8px;
        }
        .footer-links a:hover {
            text-decoration: underline;
        }
        .footer-support {
            margin-top: 12px;
            font-size: 10px;
            color: #999;
        }
        .footer-support a {
            color: #1976d2;
            text-decoration: none;
        }
        .timestamp {
            color: #999;
            font-size: 12px;
            margin-top: 16px;
            font-style: italic;
        }
        .error-message-truncated {
            max-height: 80px;
            overflow: hidden;
            position: relative;
        }
        .error-message-truncated::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 30px;
            background: linear-gradient(to bottom, transparent, #ffffff);
        }
        .expand-link {
            display: inline-block;
            margin-top: 8px;
            color: #2563eb;
            font-size: 12px;
            text-decoration: none;
            font-weight: 500;
        }
        .retry-section {
            margin-top: 0;
            margin-bottom: 0;
            padding: 20px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 14px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .retry-section.can-retry {
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
        }
        .retry-section.cannot-retry {
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
        }
        .retry-icon {
            font-size: 20px;
            flex-shrink: 0;
            line-height: 1;
            align-self: flex-start;
            margin-top: 2px;
        }
        .retry-content {
            flex: 1;
        }
        .retry-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .retry-section.can-retry .retry-title {
            color: #2e7d32;
        }
        .retry-section.cannot-retry .retry-title {
            color: #e65100;
        }
        .retry-message {
            font-size: 13px;
            line-height: 1.5;
            margin: 0;
        }
        .retry-section.can-retry .retry-message {
            color: #388e3c;
        }
        .retry-section.cannot-retry .retry-message {
            color: #f57c00;
        }
        .action-button {
            display: inline-block;
            padding: 14px 36px;
            background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
            color: #ffffff;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 15px;
            box-shadow: 0 2px 4px rgba(25, 118, 210, 0.3);
            transition: transform 0.2s;
        }
        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(25, 118, 210, 0.4);
        }
        .action-button:active {
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(25, 118, 210, 0.3);
        }
        .retry-button {
            display: inline-block;
            padding: 14px 36px;
            background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
            color: #ffffff;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 15px;
            box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .retry-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
        }
        .retry-button:active {
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
        }
    """
