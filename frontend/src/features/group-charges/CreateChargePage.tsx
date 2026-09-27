import { zodResolver } from "@hookform/resolvers/zod";
import { useId, useState } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { useNavigate } from "react-router";
import { z } from "zod";
import { getErrorMessage } from "../../api/errors";
import type { AccountPublic } from "../../api/types";
import { Alert } from "../../components/Alert";
import { AmountField } from "../../components/AmountField";
import { BottomActions } from "../../components/BottomActions";
import { Button } from "../../components/Button";
import { Checkbox } from "../../components/Checkbox";
import { XIcon } from "../../components/icons";
import { PageHeader } from "../../components/PageHeader";
import { TextField } from "../../components/TextField";
import { amountSchema, formatCOP } from "../../lib/money";
import { formatPlate } from "../../lib/plate";
import { useMyAccount } from "../accounts/api";
import { PersonRow } from "../accounts/PersonRow";
import { PlateSearch } from "../accounts/PlateSearch";
import { useCreateGroupCharge } from "./api";
import { splitMemberAmounts } from "./split";

// Same limits as the backend (GroupChargeCreate)
const chargeSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Escribe un nombre para el cobro")
    .max(100, "Máximo 100 caracteres"),
  total_amount: amountSchema,
  creator_plays: z.boolean(),
});

type ChargeForm = z.infer<typeof chargeSchema>;

export function CreateChargePage() {
  const formId = useId();
  const navigate = useNavigate();
  const { data: account } = useMyAccount();
  const createCharge = useCreateGroupCharge();
  const [members, setMembers] = useState<AccountPublic[]>([]);
  const [membersError, setMembersError] = useState<string | null>(null);

  const {
    control,
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<ChargeForm>({
    resolver: zodResolver(chargeSchema),
    defaultValues: { name: "", creator_plays: true },
  });
  const total = useWatch({ control, name: "total_amount" });
  const creatorPlays = useWatch({ control, name: "creator_plays" });
  const people = members.length + (creatorPlays ? 1 : 0);

  // Preview of each part while the total is valid; the backend does the same split when saving
  const split =
    total && members.length > 0 && total >= people
      ? splitMemberAmounts(total, members.length, creatorPlays)
      : null;

  const addMember = (member: AccountPublic) => {
    setMembers((current) => [...current, member]);
    setMembersError(null);
  };

  const validateMember = (found: AccountPublic): string | null => {
    if (found.id === account?.id) {
      return "Tú no vas en la lista. Si jugaste, marca «Yo también juego»";
    }
    if (members.some((member) => member.id === found.id)) {
      return `${found.owner_name} ya está en la lista`;
    }
    return null;
  };

  const onSubmit = handleSubmit(
    async ({ name, total_amount, creator_plays }) => {
      if (members.length === 0) {
        setMembersError("Agrega al menos una persona");
        return;
      }
      if (total_amount < people) {
        setError("total_amount", {
          message: "El total debe alcanzar al menos $1 por persona",
        });
        return;
      }
      try {
        const groupCharge = await createCharge.mutateAsync({
          name,
          total_amount,
          member_account_ids: members.map((member) => member.id),
          creator_plays,
        });
        navigate(`/charges/${groupCharge.id}`, {
          replace: true,
          state: { created: true },
        });
      } catch {
        // The error is shown from createCharge.error
      }
    },
  );

  const isInexact =
    split !== null &&
    (creatorPlays
      ? split.creatorShare !== split.memberAmounts[0]
      : split.memberAmounts[0] !==
        split.memberAmounts[split.memberAmounts.length - 1]);

  return (
    <>
      <PageHeader title="Dividir una cancha" backTo="/charges" />

      <div className="flex flex-col gap-6">
        <form
          id={formId}
          onSubmit={onSubmit}
          noValidate
          className="flex flex-col gap-4"
        >
          <TextField
            label="¿Qué cancha es?"
            placeholder="Fútbol 5 del jueves"
            maxLength={100}
            error={errors.name?.message}
            {...register("name")}
          />
          <Controller
            control={control}
            name="total_amount"
            render={({ field }) => (
              <AmountField
                label="¿Cuánto pagaste en total?"
                error={errors.total_amount?.message}
                {...field}
              />
            )}
          />
          <Checkbox
            label="Yo también juego"
            description={
              creatorPlays
                ? "El total se divide entre todos, incluyéndote. Tu parte no se le cobra a nadie."
                : "El total se divide solo entre las personas que agregues."
            }
            {...register("creator_plays")}
          />
        </form>

        <section className="flex flex-col gap-3">
          <h2 className="font-semibold text-slate-900">¿Quiénes más juegan?</h2>

          <PlateSearch
            label="Placa de la persona"
            validate={validateMember}
            onFound={addMember}
          />

          {membersError && (
            <p className="text-sm text-red-600">{membersError}</p>
          )}

          {members.length > 0 && (
            <ul className="divide-y divide-slate-100 rounded-2xl bg-white px-4 ring-1 ring-slate-200">
              {creatorPlays && account && (
                <li className="py-3">
                  <PersonRow
                    account={account}
                    isMe
                    trailing={
                      split && (
                        <div className="pr-9 text-right">
                          <p className="font-semibold text-slate-900 tabular-nums">
                            {formatCOP(split.creatorShare)}
                          </p>
                          <p className="text-xs text-slate-500">Tu parte</p>
                        </div>
                      )
                    }
                  />
                </li>
              )}
              {members.map((member, index) => (
                <li key={member.id} className="py-3">
                  <PersonRow
                    account={member}
                    trailing={
                      <div className="flex items-center gap-1">
                        {split && (
                          <span className="font-semibold text-slate-900 tabular-nums">
                            {formatCOP(split.memberAmounts[index])}
                          </span>
                        )}
                        <button
                          type="button"
                          aria-label={`Quitar a ${member.owner_name} (${formatPlate(member.plate)})`}
                          onClick={() =>
                            setMembers((current) =>
                              current.filter(({ id }) => id !== member.id),
                            )
                          }
                          className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        >
                          <XIcon className="size-4" />
                        </button>
                      </div>
                    }
                  />
                </li>
              ))}
            </ul>
          )}

          {isInexact && (
            <p className="text-xs text-slate-500">
              {creatorPlays
                ? "La división no es exacta: los pesos que sobran quedan en tu parte."
                : "La división no es exacta: los pesos que sobran los pagan los primeros de la lista."}
            </p>
          )}
        </section>

        {createCharge.error && (
          <Alert>
            <p>{getErrorMessage(createCharge.error)}</p>
          </Alert>
        )}
      </div>

      <BottomActions>
        <p className="text-center text-sm text-slate-500">
          {split
            ? `Te pagarán ${formatCOP(total - split.creatorShare)} entre ${members.length} ${members.length === 1 ? "persona" : "personas"}.`
            : "Cada persona debe pagar su parte desde su app."}
        </p>
        <Button type="submit" form={formId} disabled={createCharge.isPending}>
          {createCharge.isPending ? "Creando cobro…" : "Crear cobro"}
        </Button>
      </BottomActions>
    </>
  );
}
