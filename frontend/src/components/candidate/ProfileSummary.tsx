import { GraduationCap, Briefcase as BriefcaseIcon, FolderGit2, Award } from "lucide-react";
import { Card, CardBody, CardHeader } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import type { CandidateProfileResponse } from "../../types/candidate";

export function ProfileSummary({ profile }: { profile: CandidateProfileResponse }) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader className="flex items-center gap-2">
          <BriefcaseIcon className="h-4 w-4 text-brand-600" />
          <h3 className="text-sm font-semibold text-slate-900">Skills</h3>
        </CardHeader>
        <CardBody>
          {profile.skills.length === 0 ? (
            <EmptyState title="No skills extracted yet" description="Upload a resume to populate your skills." />
          ) : (
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((s) => (
                <Badge key={s} tone="info">
                  {s}
                </Badge>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader className="flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-brand-600" />
          <h3 className="text-sm font-semibold text-slate-900">Education</h3>
        </CardHeader>
        <CardBody>
          {profile.education.length === 0 ? (
            <EmptyState title="No education found" />
          ) : (
            <ul className="space-y-3">
              {profile.education.map((e, i) => (
                <li key={i} className="text-sm">
                  <p className="font-medium text-slate-900">{e.degree || "Degree"}{e.field ? ` · ${e.field}` : ""}</p>
                  <p className="text-slate-500">{e.institution}{e.graduation_year ? ` · ${e.graduation_year}` : ""}</p>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader className="flex items-center gap-2">
          <BriefcaseIcon className="h-4 w-4 text-brand-600" />
          <h3 className="text-sm font-semibold text-slate-900">Experience</h3>
        </CardHeader>
        <CardBody>
          {profile.experience.length === 0 ? (
            <EmptyState title="No experience found" />
          ) : (
            <ul className="space-y-4">
              {profile.experience.map((e, i) => (
                <li key={i} className="text-sm">
                  <p className="font-medium text-slate-900">{e.role || "Role"}{e.company ? ` at ${e.company}` : ""}</p>
                  {e.duration_text && <p className="text-slate-500">{e.duration_text}</p>}
                  {e.technologies.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {e.technologies.map((t) => (
                        <Badge key={t}>{t}</Badge>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader className="flex items-center gap-2">
          <FolderGit2 className="h-4 w-4 text-brand-600" />
          <h3 className="text-sm font-semibold text-slate-900">Projects</h3>
        </CardHeader>
        <CardBody>
          {profile.projects.length === 0 ? (
            <EmptyState title="No projects found" />
          ) : (
            <ul className="space-y-4">
              {profile.projects.map((p, i) => (
                <li key={i} className="text-sm">
                  <p className="font-medium text-slate-900">{p.title}</p>
                  {p.technologies.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {p.technologies.map((t) => (
                        <Badge key={t}>{t}</Badge>
                      ))}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      {profile.certifications.length > 0 && (
        <Card className="lg:col-span-2">
          <CardHeader className="flex items-center gap-2">
            <Award className="h-4 w-4 text-brand-600" />
            <h3 className="text-sm font-semibold text-slate-900">Certifications</h3>
          </CardHeader>
          <CardBody>
            <div className="flex flex-wrap gap-2">
              {profile.certifications.map((c, i) => (
                <Badge key={i} tone="neutral">
                  {c.name}{c.year ? ` (${c.year})` : ""}
                </Badge>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
