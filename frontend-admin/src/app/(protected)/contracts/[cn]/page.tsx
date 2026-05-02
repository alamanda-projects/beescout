'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { getContractByNumber } from '@/lib/api/admin'
import { getMe } from '@/lib/api/auth'
import { ImportYamlButton } from '@/components/quality/ImportYamlModal'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ArrowLeft, CheckCircle2, XCircle, Pencil } from 'lucide-react'
import Link from 'next/link'
import { formatDate } from '@/lib/utils'
import type { ModelColumn, Stakeholder } from '@/types/contract'

function BoolCell({ value }: { value?: boolean }) {
  return value
    ? <CheckCircle2 size={15} className="text-emerald-500" />
    : <XCircle size={15} className="text-slate-300" />
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex gap-3">
      <span className="text-sm text-muted-foreground w-36 shrink-0">{label}</span>
      <span className="text-sm text-slate-900 flex-1">{value ?? '-'}</span>
    </div>
  )
}

export default function AdminContractDetailPage() {
  const { cn } = useParams<{ cn: string }>()
  const router = useRouter()

  const { data: user } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const { data: contract, isLoading, isError } = useQuery({
    queryKey: ['contract', cn],
    queryFn: () => getContractByNumber(cn),
    enabled: !!cn,
  })

  if (isLoading) {
    return <div className="space-y-4 max-w-4xl"><Skeleton className="h-8 w-64" /><Skeleton className="h-10 w-full" /><Skeleton className="h-64 w-full" /></div>
  }

  if (isError || !contract) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <p className="text-lg font-medium text-slate-700">Kontrak tidak ditemukan</p>
        <Button variant="outline" className="mt-4" onClick={() => router.back()}>Kembali</Button>
      </div>
    )
  }

  const { metadata, model, ports, examples } = contract

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <Button variant="ghost" size="sm" onClick={() => router.back()} className="mb-2 -ml-2 text-muted-foreground">
          <ArrowLeft size={15} className="mr-1" /> Kembali
        </Button>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">{metadata?.name}</h2>
            <p className="text-sm text-muted-foreground mt-1">
              <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">{contract.contract_number}</code>
              {' · '}Versi {metadata?.version}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="capitalize text-sm px-3 py-1">{metadata?.type ?? '-'}</Badge>
            <ImportYamlButton context="detail" contractNumber={cn} userRole={user?.group_access as any} />
            <Button asChild size="sm" variant="outline">
              <Link href={`/contracts/${cn}/edit`}><Pencil size={14} className="mr-1.5" />Edit</Link>
            </Button>
          </div>
        </div>
      </div>

      <Tabs defaultValue="metadata">
        <TabsList>
          <TabsTrigger value="metadata">Informasi</TabsTrigger>
          <TabsTrigger value="model">Struktur Data ({model?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="ports">Koneksi ({ports?.length ?? 0})</TabsTrigger>
          <TabsTrigger value="examples">Contoh Data</TabsTrigger>
          <TabsTrigger value="raw">JSON Raw</TabsTrigger>
        </TabsList>

        <TabsContent value="metadata">
          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-3"><CardTitle className="text-base">Informasi Dasar</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <InfoRow label="Nama Kontrak" value={metadata?.name} />
                <InfoRow label="Pemilik" value={metadata?.owner} />
                <InfoRow label="Tipe" value={metadata?.type} />
                <InfoRow label="Versi" value={metadata?.version} />
                <InfoRow label="Standar Versi" value={contract.standard_version} />
                <InfoRow label="Mode Konsumsi" value={metadata?.consumption_mode} />
                {metadata?.description?.purpose && (
                  <><Separator />
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Tujuan</p>
                    <p className="text-sm">{metadata.description.purpose}</p>
                  </div></>
                )}
              </CardContent>
            </Card>

            {metadata?.sla && (
              <Card>
                <CardHeader className="pb-3"><CardTitle className="text-base">SLA</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  <InfoRow label="Ketersediaan" value={metadata.sla.availability} />
                  <InfoRow label="Frekuensi" value={metadata.sla.frequency} />
                  <InfoRow label="Retensi" value={metadata.sla.retention} />
                  <InfoRow label="Jadwal Cron" value={metadata.sla.cron} />
                </CardContent>
              </Card>
            )}

            {metadata?.stakeholders && metadata.stakeholders.length > 0 && (
              <Card>
                <CardHeader className="pb-3"><CardTitle className="text-base">Pemangku Kepentingan</CardTitle></CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow><TableHead>Nama</TableHead><TableHead>Peran</TableHead><TableHead>Email</TableHead><TableHead>Mulai</TableHead></TableRow>
                    </TableHeader>
                    <TableBody>
                      {metadata.stakeholders.map((s: Stakeholder, i: number) => (
                        <TableRow key={i}>
                          <TableCell className="font-medium">{s.name}</TableCell>
                          <TableCell>{s.role}</TableCell>
                          <TableCell className="text-muted-foreground">{s.email ?? '-'}</TableCell>
                          <TableCell className="text-muted-foreground">{formatDate(s.date_in)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="model">
          <Card>
            <CardContent className="pt-4">
              {!model || model.length === 0 ? (
                <p className="text-sm text-muted-foreground py-8 text-center">Tidak ada definisi kolom.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Kolom</TableHead>
                      <TableHead>Nama Bisnis</TableHead>
                      <TableHead>Tipe</TableHead>
                      <TableHead className="text-center">PK</TableHead>
                      <TableHead className="text-center">PII</TableHead>
                      <TableHead className="text-center">Wajib</TableHead>
                      <TableHead className="text-center">Nullable</TableHead>
                      <TableHead>Deskripsi</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {model.map((col: ModelColumn) => (
                      <TableRow key={col.column}>
                        <TableCell><code className="text-xs font-mono">{col.column}</code></TableCell>
                        <TableCell className="text-sm">{col.business_name ?? '-'}</TableCell>
                        <TableCell><Badge variant="outline" className="text-xs font-mono">{col.logical_type ?? '-'}</Badge></TableCell>
                        <TableCell className="text-center"><BoolCell value={col.is_primary} /></TableCell>
                        <TableCell className="text-center"><BoolCell value={col.is_pii} /></TableCell>
                        <TableCell className="text-center"><BoolCell value={col.is_mandatory} /></TableCell>
                        <TableCell className="text-center"><BoolCell value={col.is_nullable} /></TableCell>
                        <TableCell className="text-sm text-muted-foreground max-w-xs">{col.description ?? '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ports">
          <div className="space-y-3">
            {!ports || ports.length === 0 ? (
              <Card><CardContent className="py-8 text-center text-muted-foreground text-sm">Tidak ada informasi koneksi.</CardContent></Card>
            ) : ports.map((port, i) => (
              <Card key={i}>
                <CardHeader className="pb-3"><CardTitle className="text-sm">{port.object}</CardTitle></CardHeader>
                {port.properties && port.properties.length > 0 && (
                  <CardContent className="pt-0 space-y-2">
                    {port.properties.map((p, j) => <InfoRow key={j} label={p.name} value={p.value} />)}
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="examples">
          <Card>
            <CardContent className="pt-6">
              {!examples?.data ? (
                <p className="text-sm text-muted-foreground text-center py-4">Tidak ada contoh data.</p>
              ) : (
                <pre className="text-xs bg-slate-50 border rounded-lg p-4 overflow-auto max-h-96">
                  {JSON.stringify(examples.data, null, 2)}
                </pre>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="raw">
          <Card>
            <CardHeader className="pb-3"><CardTitle className="text-base">JSON Raw</CardTitle></CardHeader>
            <CardContent>
              <pre className="text-xs bg-slate-50 border rounded-lg p-4 overflow-auto max-h-[500px]">
                {JSON.stringify(contract, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
