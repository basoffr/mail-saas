import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  Mail,
  TestTube,
  Power,
  Loader2,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { MailAccountOut } from '@/types/inbox';
import { inboxService } from '@/services/inbox';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';

export function ImapAccountsSection() {
  const { toast } = useToast();
  const [accounts, setAccounts] = useState<MailAccountOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingAccount, setTestingAccount] = useState<string | null>(null);
  const [togglingAccount, setTogglingAccount] = useState<string | null>(null);

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const response = await inboxService.getAccounts();
      setAccounts(Array.isArray(response?.items) ? response.items : []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load IMAP accounts',
        variant: 'destructive'
      });
      setAccounts([]); // Ensure empty array on error
    } finally {
      setLoading(false);
    }
  };

  const handleTestAccount = async (accountId: string) => {
    setTestingAccount(accountId);
    try {
      const response = await inboxService.testAccount(accountId);
      toast({
        title: response.ok ? 'Connection Successful' : 'Connection Failed',
        description: response.message,
        variant: response.ok ? 'default' : 'destructive'
      });
    } catch (error) {
      toast({
        title: 'Test Failed',
        description: 'Failed to test IMAP connection',
        variant: 'destructive'
      });
    } finally {
      setTestingAccount(null);
    }
  };

  const handleToggleAccount = async (accountId: string) => {
    setTogglingAccount(accountId);
    try {
      await inboxService.toggleAccount(accountId);
      await fetchAccounts(); // Refresh to show updated state
      toast({
        title: 'Success',
        description: 'Account status updated',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update account status',
        variant: 'destructive'
      });
    } finally {
      setTogglingAccount(null);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: nl });
  };

  const getStatusBadge = (account: MailAccountOut) => {
    if (account.active) {
      return (
        <Badge className="bg-green-100 text-green-800">
          <CheckCircle className="w-3 h-3 mr-1" />
          Active
        </Badge>
      );
    } else {
      return (
        <Badge variant="outline" className="text-gray-600">
          <XCircle className="w-3 h-3 mr-1" />
          Inactive
        </Badge>
      );
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Mail className="h-4 w-4" />
          <span className="font-medium">IMAP Accounts</span>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Mail className="h-4 w-4" />
          <span className="font-medium">IMAP Accounts</span>
        </div>
        <Badge variant="outline" className="text-xs">
          {(accounts ?? []).filter(acc => acc?.active).length} active
        </Badge>
      </div>

      {(accounts ?? []).length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <Mail className="w-12 h-12 mx-auto mb-4 opacity-20" />
          <p className="font-medium">No IMAP accounts configured</p>
          <p className="text-sm">IMAP accounts will be configured via backend settings</p>
        </div>
      ) : (
        <div className="rounded-lg border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30">
                <TableHead>Account</TableHead>
                <TableHead>Host</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Fetch</TableHead>
                <TableHead>Last UID</TableHead>
                <TableHead className="w-32">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(accounts ?? []).map((account) => (
                <TableRow key={account.id} className="hover:bg-muted/20">
                  <TableCell>
                    <div>
                      <div className="font-medium">{account.label}</div>
                      <div className="text-sm text-muted-foreground font-mono">
                        {account.usernameMasked}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="font-mono text-sm">
                      <div>{account.imapHost}:{account.imapPort}</div>
                      {account.useSsl && (
                        <Badge variant="outline" className="text-xs mt-1">
                          SSL
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(account)}
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatDate(account.lastFetchAt)}
                  </TableCell>
                  <TableCell className="text-sm font-mono">
                    {account.lastSeenUid || '-'}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTestAccount(account.id)}
                        disabled={testingAccount === account.id}
                        className="h-7 px-2"
                      >
                        {testingAccount === account.id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <TestTube className="w-3 h-3" />
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggleAccount(account.id)}
                        disabled={togglingAccount === account.id}
                        className="h-7 px-2"
                      >
                        {togglingAccount === account.id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Power className="w-3 h-3" />
                        )}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <div className="text-xs text-muted-foreground space-y-1">
        <div className="flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          <span>IMAP credentials are stored securely and never displayed in plaintext</span>
        </div>
        <div>
          <span className="font-medium">Test:</span> Verify IMAP connection settings
        </div>
        <div>
          <span className="font-medium">Toggle:</span> Enable/disable account for inbox fetching
        </div>
      </div>
    </div>
  );
}
