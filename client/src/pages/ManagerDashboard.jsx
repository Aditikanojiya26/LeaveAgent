import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
    getManagerLeaveRequests,
    decideLeaveRequest,
} from "../api/managerApi";

export default function ManagerDashboard() {
    const queryClient = useQueryClient();

    const { data: requests = [], isLoading } = useQuery({
        queryKey: ["manager-leave-requests"],
        queryFn: getManagerLeaveRequests,
    });

    const decisionMutation = useMutation({
        mutationFn: decideLeaveRequest,
        onSuccess: () => {
            queryClient.invalidateQueries(["manager-leave-requests"]);
        },
    });

    const handleDecision = (leaveId, decision) => {
        decisionMutation.mutate({
            leaveId,
            decision,
            reason:
                decision === "APPROVED"
                    ? "Approved by manager"
                    : "Rejected by manager",
        });
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-[#111] flex items-center justify-center text-neutral-500 text-sm">
                Loading leave requests...
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#111] text-neutral-200 p-6 font-sans">

            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <h1 className="text-xl font-semibold text-white tracking-tight">
                    Leave Requests
                </h1>
                {requests.length > 0 && (
                    <span className="text-xs font-medium px-3 py-1 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-900">
                        {requests.length} Pending
                    </span>
                )}
            </div>

            {requests.length === 0 ? (
                <div className="text-center py-20 text-neutral-600 text-sm">
                    No pending leave requests.
                </div>
            ) : (
                <div className="grid grid-cols-2 gap-4 w-full items-start">
                    {requests.map((leave) => {
                        const initials = `E${String(leave.employee_id).slice(-1)}`;
                        const riskColor =
                            leave.ai_risk === "Low"
                                ? "text-emerald-400"
                                : leave.ai_risk === "High"
                                ? "text-red-400"
                                : "text-amber-400";
                        const recColor =
                            leave.ai_recommendation === "APPROVED"
                                ? "text-emerald-400"
                                : "text-red-400";

                        return (
                            <div
                                key={leave.id}
                                className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl p-5"
                            >
                                {/* Card Header */}
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-[#2a2a2a] flex items-center justify-center text-sm font-semibold text-neutral-400">
                                            {initials}
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-neutral-100">
                                                <p>Employee: {leave.employee_name}</p>
                                            </p>
                                            
                                            <p className="text-xs text-neutral-500 mt-0.5">
                                                Leave type:{" "}
                                                <span className="text-blue-400 font-medium">
                                                    {leave.leave_type}
                                                </span>
                                            </p>
                                        </div>
                                    </div>
                                    <span className="text-[11px] font-medium px-2.5 py-1 rounded-full bg-amber-950 text-amber-400 border border-amber-900">
                                        Pending
                                    </span>
                                </div>

                                {/* Date & Reason */}
                                <div className="flex gap-6 mb-3 flex-wrap">
                                    <div>
                                        <p className="text-[10px] text-neutral-600 uppercase tracking-wide mb-0.5">Start date</p>
                                        <p className="text-sm font-medium text-neutral-300">{leave.start_date}</p>
                                    </div>
                                    <div>
                                        <p className="text-[10px] text-neutral-600 uppercase tracking-wide mb-0.5">End date</p>
                                        <p className="text-sm font-medium text-neutral-300">{leave.end_date}</p>
                                    </div>
                                </div>
                                <div className="mb-4">
                                    <p className="text-[10px] text-neutral-600 uppercase tracking-wide mb-0.5">Reason</p>
                                    <p className="text-sm text-neutral-400">{leave.reason}</p>
                                </div>

                                {/* AI Box */}
                                <div className="bg-[#141414] border border-[#222] rounded-xl p-4 mb-4">
                                    <p className="text-[10px] text-neutral-600 uppercase tracking-wide flex items-center gap-1.5 mb-3">
                                        <span className="w-1.5 h-1.5 rounded-full bg-purple-500 inline-block" />
                                        AI Analysis
                                    </p>

                                    <div className="grid grid-cols-2 gap-3 mb-3">
                                        <div>
                                            <p className="text-[11px] text-neutral-600 mb-0.5">Recommendation</p>
                                            <p className={`text-sm font-medium ${recColor}`}>
                                                {leave.ai_recommendation}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-[11px] text-neutral-600 mb-0.5">Risk</p>
                                            <p className={`text-sm font-medium ${riskColor}`}>
                                                {leave.ai_risk}
                                            </p>
                                        </div>
                                        <div className="col-span-2">
                                            <p className="text-[11px] text-neutral-600 mb-0.5">Reason</p>
                                            <p className="text-xs text-neutral-400">{leave.ai_reason}</p>
                                        </div>
                                    </div>

                                    {/* Blockers */}
                                    <p className="text-[11px] text-neutral-600 mb-1.5">Blockers</p>
                                    <div className="space-y-1">
                                        {leave.ai_blockers?.length ? (
                                            leave.ai_blockers.map((b, index) => (
                                                <div
                                                    key={index}
                                                    className="flex items-center gap-2 text-xs text-neutral-400 py-1 border-b border-[#1e1e1e] last:border-0"
                                                >
                                                    <span className="w-1 h-1 rounded-full bg-neutral-600 flex-shrink-0" />
                                                    {typeof b === "string" ? (
                                                        b
                                                    ) : (
                                                        <>
                                                            <span className="text-neutral-200 font-medium">{b.type}</span>
                                                            {b.title && ` — ${b.title}`}
                                                            {b.priority && (
                                                                <span className="ml-auto text-[10px] text-neutral-600">
                                                                    {b.priority}
                                                                </span>
                                                            )}
                                                        </>
                                                    )}
                                                </div>
                                            ))
                                        ) : (
                                            <p className="text-xs text-neutral-600">None</p>
                                        )}
                                    </div>

                                    {/* Suggestion */}
                                    {leave.ai_suggestion && (
                                        <div className="mt-3 px-3 py-2 bg-indigo-950 border border-indigo-900 rounded-lg text-xs text-indigo-400">
                                            {leave.ai_suggestion}
                                        </div>
                                    )}
                                </div>

                                {/* Actions */}
                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={() => handleDecision(leave.id, "APPROVED")}
                                        disabled={decisionMutation.isPending}
                                        className="px-5 py-2 rounded-xl text-sm font-medium bg-emerald-950 text-emerald-400 border border-emerald-900 hover:bg-emerald-900 transition-colors disabled:opacity-50"
                                    >
                                        Approve
                                    </button>
                                    <button
                                        onClick={() => handleDecision(leave.id, "REJECTED")}
                                        disabled={decisionMutation.isPending}
                                        className="px-5 py-2 rounded-xl text-sm font-medium bg-red-950 text-red-400 border border-red-900 hover:bg-red-900 transition-colors disabled:opacity-50"
                                    >
                                        Reject
                                    </button>
                                    <span className="ml-auto text-xs text-neutral-600">
                                        Decision logged automatically
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}