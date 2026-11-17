package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * Null-guard for Goety's HellBlast explosion (the "Ticking entity" NPE family).
 *
 * Crash chain being fixed (Goety 2.5.25 - 2.5.58.4, checked class by class):
 *   HellBlast.m_6532_(HitResult) creates an anonymous SpellExplosion subclass and
 *   captures the projectile's owner into it. When that explosion damages something,
 *   the subclass' explodeHurt() ignites the captured owner:
 *
 *     Entity owner = this.val$entity;                 // getOwner(), null when ownerless
 *     if (src.m_7640_() instanceof HellBlast hb && hb.getFiery() > 0) {
 *         owner.m_20254_(5 * hb.getFiery());          // HellBlast.java:177 -> NPE
 *     }
 *
 *   An OWNERLESS HellBlast (built that way by the Lavaball / Meteor Shower spells, and
 *   by /summon goety:hell_blast) therefore crashes the server the moment its explosion
 *   hurts a living entity. Exploding in empty air does NOT trigger it.
 *
 * Why the guard must sit on that call site:
 *   SpellExplosion.<init> itself calls explodeHurt (SpellExplosion.java:72), so the
 *   exception is thrown from inside the constructor and the constructor never returns.
 *   A guard placed at @At("RETURN") of the constructor can never run - that was the
 *   mistake in goetyhellblastfix 0.0.1, confirmed against a real crash report:
 *     HellBlast$1.explodeHurt(HellBlast.java:177)
 *     SpellExplosion.<init>(SpellExplosion.java:72)
 *     HellBlast$1.<init>(HellBlast.java:171)
 *     HellBlast.m_6532_(HellBlast.java:171)
 *   The same report also proves the class name is stable: it reads HellBlast$1, not a
 *   mixin-renamed HellBlast$Anonymous$hash (that rename applies to anonymous classes
 *   generated INSIDE other mods' mixins, not to Goety's).
 *
 * What this does: redirects the single Entity.m_20254_(I) (setRemainingFireTicks) call
 * inside HellBlast$1.explodeHurt and skips it when the captured owner is null. The
 * super call that applies the explosion damage runs first and is untouched, so an
 * owned HellBlast behaves byte-for-byte the same. Mixin-only, no Goety code.
 *
 * SRG names on purpose: this project compiles against the SRG client jar and runs in a
 * production (SRG) environment, so m_20254_ is written literally and remap=false keeps
 * the injector from re-mapping it. require = 0 (plus the config's defaultRequire=0 and
 * required=false) keeps the soft mode: if a future Goety release drops the call, this
 * redirect is skipped with a warning instead of crashing the game.
 */
@Mixin(targets = "com.Polarice3.Goety.common.entities.projectiles.HellBlast$1", remap = false)
public class HellBlastExplosionNullGuardMixin {

    @Redirect(
        method = "explodeHurt",
        at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/Entity;m_20254_(I)V", remap = false),
        require = 0,
        remap = false
    )
    private void goetyfix$skipNullOwnerFire(Entity owner, int ticks) {
        if (owner != null) {
            owner.m_20254_(ticks);
        }
    }
}
